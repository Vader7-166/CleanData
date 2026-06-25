#!/usr/bin/env python3
"""
dict_enhancer.py - Phân tích disagreement dict vs AI,
sinh đề xuất cải thiện dictionary và dữ liệu retrain.

Đầu vào:
  - DataFrame raw (Detailed_Product, HS_Code, ...)
  - Kết quả dict matching (dict_label, dict_conf, dict_status)
  - Kết quả AI inference (ai_label, ai_conf, ai_status, ai_embeddings)

Đầu ra:
  - dict_enhancement_proposals.csv - đề xuất keyword mới
  - hard_cases.csv - case cần review thủ công
  - train_phase6_augmented.csv - dữ liệu retrain
  - dict_enhancement_report.txt - báo cáo tổng hợp
"""

import os
import sys
import json
import time
import math
import re
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

LABEL_STANDARD_PATH = os.path.join(BASE_DIR, "config", "label_standard.json")
DICT_PATH = os.path.join(BASE_DIR, "dataset", "DICT_HQ_2026_v2.csv")


def load_label_standard():
    with open(LABEL_STANDARD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_label(d_sp, loai, l1, l2, aliases):
    d_sp = str(d_sp).strip()
    lo = str(loai).strip()
    lp1 = str(l1).strip()
    lp2 = str(l2).strip()
    d_sp = aliases["dong_sp"].get(d_sp, d_sp)
    lo = aliases["loai"].get(lo, lo)
    lp1 = aliases["lop1"].get(lp1, lp1.lower())
    lp2 = aliases["lop2"].get(lp2, lp2.lower())
    d_sp = "không_có" if d_sp in ("nan", "None", "0", "") else d_sp
    lo = "không_có" if lo in ("nan", "None", "0", "") else lo
    lp1 = "không_có" if lp1 in ("nan", "None", "0", "") else lp1
    lp2 = "không_có" if lp2 in ("nan", "None", "0", "") else lp2
    return d_sp, lo, lp1, lp2


def split_label(label_str, aliases):
    if pd.isna(label_str) or str(label_str).strip() == "":
        return "không_có", "không_có", "không_có", "không_có"
    parts = str(label_str).split(" | ")
    d_sp = parts[0] if len(parts) > 0 else "không_có"
    loai = parts[1] if len(parts) > 1 else "không_có"
    l1 = parts[2] if len(parts) > 2 else "không_có"
    l2 = parts[3] if len(parts) > 3 else "không_có"
    return normalize_label(d_sp, loai, l1, l2, aliases)


def signature_of(label_str):
    """Tạo chữ ký rút gọn để so sánh label (bỏ không_có)."""
    parts = str(label_str).split(" | ")
    return "|".join(p for p in parts if p.lower() != "không_có" and p.strip())


class DictEnhancer:
    PATTERN_LABELS = {
        "verified": "Dict=AI=GT (Verified)",
        "dict_fail_ai_pass": "Dict fail, AI pass -> Add to dict",
        "dict_pass_ai_fail": "Dict pass, AI fail -> Retrain model",
        "both_fail": "Both fail -> Hard case, manual review",
        "dict_wrong_ai_wrong": "Both wrong -> Hard case",
        "conflict": "Dict != AI, unknown GT -> Review",
    }

    def __init__(self, get_embedding_fn=None, output_dir=None):
        self.get_embedding_fn = get_embedding_fn
        self.output_dir = output_dir or os.path.join(BASE_DIR, "analysis", "output")
        os.makedirs(self.output_dir, exist_ok=True)
        self.std = load_label_standard()
        self.label_aliases = {
            "dong_sp": self.std.get("dong_sp", {}).get("aliases", {}),
            "loai": self.std.get("loai", {}).get("aliases", {}),
            "lop1": self.std.get("lop1", {}).get("aliases", {}),
            "lop2": self.std.get("lop2", {}).get("aliases", {}),
        }

    def classify_disagreements(self, df, dict_label_col="dict_label", ai_label_col="ai_label",
                               ai_conf_col="ai_conf"):
        rows = []
        for idx, row in df.iterrows():
            raw_text = str(row.get("Detailed_Product", row.get("text", "")))
            hs_code = str(row.get("HS_Code", ""))
            dict_lbl = row.get(dict_label_col)
            ai_lbl = row.get(ai_label_col)
            ai_conf = row.get(ai_conf_col, 0)
            gt_lbl = row.get("combined_label", row.get("ground_truth", None))

            if pd.notna(dict_lbl):
                dict_dsp, dict_lo, dict_l1, dict_l2 = split_label(dict_lbl, self.label_aliases)
                dict_norm = f"{dict_dsp} | {dict_lo} | {dict_l1} | {dict_l2}"
            else:
                dict_norm = None

            if pd.notna(ai_lbl):
                ai_dsp, ai_lo, ai_l1, ai_l2 = split_label(ai_lbl, self.label_aliases)
                ai_norm = f"{ai_dsp} | {ai_lo} | {ai_l1} | {ai_l2}"
            else:
                ai_norm = None

            if gt_lbl and pd.notna(gt_lbl):
                gt_dsp, gt_lo, gt_l1, gt_l2 = split_label(gt_lbl, self.label_aliases)
                gt_norm = f"{gt_dsp} | {gt_lo} | {gt_l1} | {gt_l2}"
            else:
                gt_norm = None

            dict_ok = dict_norm is not None and (gt_norm is None or dict_norm == gt_norm)
            ai_ok = ai_norm is not None and (gt_norm is None or ai_norm == gt_norm)

            if dict_ok and ai_ok:
                pattern = "verified"
                detail = "Both agree and correct"
            elif not dict_ok and ai_ok and gt_norm is not None:
                pattern = "dict_fail_ai_pass"
                detail = f"Dict={dict_norm}, AI={ai_norm}, GT={gt_norm}"
            elif dict_ok and not ai_ok and gt_norm is not None:
                pattern = "dict_pass_ai_fail"
                detail = f"Dict={dict_norm}, AI={ai_norm}, GT={gt_norm}"
            elif not dict_ok and not ai_ok and gt_norm is not None:
                pattern = "both_fail"
                detail = f"Dict={dict_norm}, AI={ai_norm}, GT={gt_norm}"
            elif dict_norm is not None and ai_norm is not None and dict_norm != ai_norm and gt_norm is None:
                pattern = "conflict"
                detail = f"Dict={dict_norm}, AI={ai_norm}, no GT"
            else:
                pattern = "verified"
                detail = "Not classified"

            rows.append({
                "idx": idx,
                "product": str(raw_text)[:200],
                "HS_Code": hs_code,
                "dict_label": dict_norm,
                "ai_label": ai_norm,
                "ground_truth": gt_norm,
                "pattern": pattern,
                "detail": detail,
                "ai_conf": ai_conf,
            })
        result_df = pd.DataFrame(rows)
        return result_df

    def propose_dict_keywords(self, disagreement_df, raw_df, min_confidence=0.8):
        target = disagreement_df[disagreement_df["pattern"] == "dict_fail_ai_pass"]
        target = target[target["ai_conf"] >= min_confidence]

        if target.empty:
            return pd.DataFrame()

        proposals = []
        for _, row in target.iterrows():
            ai_parts = row["ai_label"].split(" | ")
            while len(ai_parts) < 4:
                ai_parts.append("không_có")

            ai_dsp, ai_lo, ai_l1, ai_l2 = ai_parts[:4]
            raw_text = row["product"]
            hs = row["HS_Code"]

            hs_prefix = re.sub(r"\D", "", str(hs))[:4] if hs and str(hs).strip() else ""

            proposals.append({
                "product": raw_text,
                "HS_Code": hs,
                "HS_prefix": hs_prefix,
                "suggested_Dong_SP": ai_dsp,
                "suggested_Loai": ai_lo,
                "suggested_Lop1": ai_l1,
                "suggested_Lop2": ai_l2,
                "ai_conf": row["ai_conf"],
                "detail": row["detail"],
            })

        prop_df = pd.DataFrame(proposals)

        if self.get_embedding_fn is not None and not prop_df.empty:
            prop_df = self._deduplicate_by_semantics(prop_df)

        return prop_df

    def _deduplicate_by_semantics(self, prop_df):
        try:
            texts = prop_df["product"].tolist()
            embs = self.get_embedding_fn(texts)
            if embs is None:
                return prop_df
            embs = np.asarray(embs)
            keep = [True] * len(prop_df)
            for i in range(len(prop_df)):
                if not keep[i]:
                    continue
                for j in range(i + 1, len(prop_df)):
                    if not keep[j]:
                        continue
                    sim = float(embs[i] @ embs[j])
                    if sim > 0.85:
                        same_label = (
                            prop_df.iloc[i]["suggested_Lop1"] == prop_df.iloc[j]["suggested_Lop1"]
                        )
                        if same_label:
                            if prop_df.iloc[j]["ai_conf"] > prop_df.iloc[i]["ai_conf"]:
                                keep[i] = False
                            else:
                                keep[j] = False
            return prop_df[keep].reset_index(drop=True)
        except Exception as e:
            print(f"DEBUG: Semantic deduplication failed: {e}")
            return prop_df

    def generate_hard_cases(self, disagreement_df):
        hard = disagreement_df[disagreement_df["pattern"] == "both_fail"]
        return hard.copy()

    def generate_training_data(self, disagreement_df, raw_df, min_confidence=0.75):
        train_rows = []
        patterns_to_use = ["dict_fail_ai_pass", "dict_pass_ai_fail"]
        target = disagreement_df[disagreement_df["pattern"].isin(patterns_to_use)]

        for _, row in target.iterrows():
            if row["pattern"] == "dict_fail_ai_pass" and row["ai_conf"] >= min_confidence:
                label = row["ai_label"]
                conf = row["ai_conf"]
                source = "phase6_ai_correct"
            elif row["pattern"] == "dict_pass_ai_fail":
                label = row["dict_label"]
                conf = 1.0
                source = "phase6_dict_correct"
            else:
                continue

            labels = label.split(" | ") if label else ["không_có"] * 4
            while len(labels) < 4:
                labels.append("không_có")

            if any(l == "không_có" for l in labels[:2]):
                continue

            train_rows.append({
                "text": f"san pham: {row['product']}",
                "Dong SP": labels[0],
                "Loai": labels[1],
                "Lop 1": labels[2],
                "Lop 2": labels[3],
                "combined_label": label,
                "weight": round(conf, 2),
                "source": source,
                "HS_Code": row["HS_Code"],
            })

            kw_variants = self._generate_variants(row["product"])
            for v in kw_variants:
                train_rows.append({
                    "text": f"san pham: {v}",
                    "Dong SP": labels[0],
                    "Loai": labels[1],
                    "Lop 1": labels[2],
                    "Lop 2": labels[3],
                    "combined_label": label,
                    "weight": round(conf * 0.5, 2),
                    "source": f"{source}_variant",
                    "HS_Code": row["HS_Code"],
                })

        return pd.DataFrame(train_rows)

    def _generate_variants(self, text, max_variants=3):
        text = str(text).lower().strip()
        variants = set()
        parts = text.split()
        n = len(parts)
        if n >= 4:
            variants.add(" ".join(parts[:3]))
            variants.add(" ".join(parts[:2] + parts[-1:]))
        if n >= 3:
            variants.add(" ".join(parts[1:]))
        comma_split = re.split(r"[,;/]", text)
        for s in comma_split:
            s = s.strip()
            if len(s.split()) >= 2:
                variants.add(s)
        variants = [v for v in variants if len(v.split()) >= 2 and v != text]
        return list(variants)[:max_variants]

    def export_suggestions(self, prop_df, hard_df, train_df, prefix=""):
        out_dir = self.output_dir

        if not prop_df.empty:
            prop_path = os.path.join(out_dir, f"{prefix}dict_enhancement_proposals.csv")
            prop_df.to_csv(prop_path, index=False, encoding="utf-8-sig")
            print(f"  Dict enhancement proposals: {len(prop_df)} rows -> {prop_path}")

        if not hard_df.empty:
            hard_path = os.path.join(out_dir, f"{prefix}hard_cases.csv")
            hard_df.to_csv(hard_path, index=False, encoding="utf-8-sig")
            print(f"  Hard cases: {len(hard_df)} rows -> {hard_path}")

        if not train_df.empty:
            train_path = os.path.join(out_dir, f"{prefix}train_phase6_augmented.csv")
            train_df.to_csv(train_path, index=False, encoding="utf-8-sig")
            print(f"  Retrain data: {len(train_df)} rows -> {train_path}")

    def generate_report(self, disagreement_df, prop_df, hard_df, train_df, prefix=""):
        total = len(disagreement_df)
        pattern_counts = disagreement_df["pattern"].value_counts()
        dsp_covered = disagreement_df[disagreement_df["pattern"] != "verified"]["pattern"].value_counts()

        lines = []
        lines.append("=" * 70)
        lines.append("  DICT ENHANCER REPORT")
        lines.append(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)
        lines.append(f"\nTotal rows analyzed: {total}")
        lines.append(f"\n--- Disagreement Patterns ---")
        for p, cnt in pattern_counts.items():
            pct = 100 * cnt / total if total > 0 else 0
            label = self.PATTERN_LABELS.get(p, p)
            lines.append(f"  {label:<50s}: {cnt:>6,} ({pct:>5.1f}%)")

        lines.append(f"\n--- Enhancement Potential ---")
        ai_pass = pattern_counts.get("dict_fail_ai_pass", 0)
        if ai_pass > 0:
            lines.append(f"  Dict entries can be enhanced from AI passes: {ai_pass:,}")
        if not prop_df.empty:
            deduped = len(prop_df)
            lines.append(f"  Unique keyword proposals after semantic dedup: {deduped:,}")

        both_fail = pattern_counts.get("both_fail", 0)
        if both_fail > 0:
            lines.append(f"  Hard cases needing manual review: {both_fail:,}")

        lines.append(f"\n--- Retraining Data ---")
        if not train_df.empty:
            sources = train_df["source"].value_counts()
            lines.append(f"  Total retrain samples: {len(train_df):,}")
            for src, cnt in sources.items():
                lines.append(f"    {src}: {cnt}")
        else:
            lines.append(f"  No retraining data generated.")

        lines.append(f"\n{'=' * 70}")
        report = "\n".join(lines)

        report_path = os.path.join(self.output_dir, f"{prefix}dict_enhancement_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(report)
        return report


def run_enhancement(df_raw, df_dict_result, df_ai_result, get_embedding_fn=None,
                    output_dir=None, prefix="", ground_truth_col=None):
    enhancer = DictEnhancer(get_embedding_fn=get_embedding_fn, output_dir=output_dir)

    merged = df_raw.copy()
    for col in df_dict_result.columns:
        merged[f"dict_{col}"] = df_dict_result[col].values if col in df_dict_result.columns else None
    for col in df_ai_result.columns:
        merged[f"ai_{col}"] = df_ai_result[col].values if col in df_ai_result.columns else None

    if ground_truth_col and ground_truth_col in merged.columns:
        merged["combined_label"] = merged[ground_truth_col]
    else:
        merged["combined_label"] = None

    disagreement_df = enhancer.classify_disagreements(
        merged,
        dict_label_col="dict_label",
        ai_label_col="ai_label",
        ai_conf_col="ai_conf",
    )

    prop_df = enhancer.propose_dict_keywords(disagreement_df, merged)
    hard_df = enhancer.generate_hard_cases(disagreement_df)
    train_df = enhancer.generate_training_data(disagreement_df, merged)
    enhancer.export_suggestions(prop_df, hard_df, train_df, prefix=prefix)
    enhancer.generate_report(disagreement_df, prop_df, hard_df, train_df, prefix=prefix)

    return {
        "disagreement": disagreement_df,
        "proposals": prop_df,
        "hard_cases": hard_df,
        "train_data": train_df,
    }
