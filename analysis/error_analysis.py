#!/usr/bin/env python3
"""
Phase 1 - Error Analysis: Phan tich loi chi tiet cho Pipeline Classification.

Chay Dict Matcher + AI Model tren test set tu notebook split (HQ 2025.xlsx),
so sanh voi ground truth de:
1. Breakdown accuracy tung cap: Dong SP, Loai, Lop 1, Lop 2
2. Confusion matrix top-20 class bi confuse -> heatmap
3. Dict vs AI ratio + overlap analysis
4. Calibration curve -> optimal threshold

Usage:
    python analysis/error_analysis.py
    python analysis/error_analysis.py --max-rows 5000
    python analysis/error_analysis.py --dict-paths dataset/DICT_HQ_2026.csv
"""

import argparse
import os
import sys
import time
import pickle
import json
import re
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(BASE_DIR, "working"))
TRAIN_DATA = os.path.join(BASE_DIR, "dataset", "HQ 2025.xlsx")
DEFAULT_DICT_PATHS = [
    os.path.join(BASE_DIR, "dataset", "DICT_HQ_2026.csv"),
    os.path.join(BASE_DIR, "dataset", "dictv3.csv"),
]
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "output")
LABEL_STANDARD_PATH = os.path.join(BASE_DIR, "config", "label_standard.json")
RANDOM_STATE = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
    return ' '.join(text.split()).strip()


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


def load_and_split_data(xlsx_path, max_test_rows=None):
    print(f"Loading training data from {xlsx_path}...")
    df = pd.read_excel(xlsx_path)

    df = df.dropna(subset=['Tên hàng'])
    df = df.fillna('')

    cols_to_predict = ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']
    for col in cols_to_predict:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].astype(str).replace('', 'không_có')

    df['text'] = "Hãng: " + df['Hãng'].astype(str) + " - Công suất: " + df['Công suất'].astype(str) + " - Sản phẩm: " + df['Tên hàng'].astype(str)
    df['text'] = df['text'].apply(clean_text)
    df = df[df['text'] != '']

    df['combined_label'] = (
        df['Dòng SP'] + " | " + df['Loại'] + " | " + df['Lớp 1'] + " | " + df['Lớp 2']
    )

    label_counts = df['combined_label'].value_counts()
    valid_labels = label_counts[label_counts >= 5].index
    df = df[df['combined_label'].isin(valid_labels)]

    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    df['label'] = label_encoder.fit_transform(df['combined_label'])
    num_labels = len(label_encoder.classes_)
    print(f"Total unique labels: {num_labels} | Rows after filtering: {len(df)}")

    from sklearn.model_selection import train_test_split
    train_df, temp_df = train_test_split(
        df[['text', 'label', 'Tên hàng', 'combined_label',
            'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Hãng', 'Công suất', 'Mã HS']],
        test_size=0.2, random_state=RANDOM_STATE
    )
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=RANDOM_STATE)

    print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    if max_test_rows and max_test_rows < len(test_df):
        test_df = test_df.sample(n=max_test_rows, random_state=RANDOM_STATE)

    return test_df


def load_model_and_encoder(model_path):
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch

    print(f"Loading tokenizer from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)

    print(f"Loading model from {model_path}...")
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    device = torch.device("cpu")
    model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
    model.to(device)
    model.eval()

    with open(os.path.join(model_path, "label_encoder.pkl"), "rb") as f:
        label_encoder = pickle.load(f)

    return tokenizer, model, label_encoder, device


def run_dict_predictions(df, dict_paths):
    from backend.core.dictionary_matcher import DictionaryMatcher

    matcher = DictionaryMatcher(dict_paths=dict_paths)

    results = []
    total = len(df)
    for i, (_, row) in enumerate(df.iterrows()):
        input_text = row.get("text", "")
        if not input_text:
            input_text = "Hãng: " + str(row.get("Hãng", "")) + " - Công suất: " + str(row.get("Công suất", "")) + " - Sản phẩm: " + str(row.get("Tên hàng", ""))
            input_text = clean_text(input_text)

        label, score, status = matcher.predict(input_text)
        results.append({
            "dict_label": label if pd.notna(label) else None,
            "dict_score": score,
            "dict_status": status,
        })

        if (i + 1) % 5000 == 0:
            print(f"  Dict: {i + 1}/{total} rows processed...")

    return pd.DataFrame(results)


def run_ai_predictions(df, tokenizer, model, label_encoder, device):
    import torch
    import torch.nn.functional as F

    texts = df["text"].tolist()
    max_length = 64
    batch_size = 64
    threshold = 0.85

    all_labels = []
    all_confs = []
    all_statuses = []

    total = len(texts)
    start = time.time()

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        inputs = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        probs = F.softmax(outputs.logits, dim=-1)
        max_probs, pred_ids = torch.max(probs, dim=-1)

        max_probs_np = max_probs.cpu().numpy()
        pred_ids_np = pred_ids.cpu().numpy()
        labels = label_encoder.inverse_transform(pred_ids_np)

        for prob, label in zip(max_probs_np, labels):
            status = "Tự động duyệt (AI)" if prob >= threshold else "Cần kiểm tra"
            all_labels.append(label)
            all_confs.append(round(float(prob) * 100, 2))
            all_statuses.append(status)

        if (i + batch_size) % (batch_size * 20) == 0 or i == 0:
            elapsed = time.time() - start
            rows_done = min(i + batch_size, total)
            rate = rows_done / elapsed if elapsed > 0 else 0
            print(f"  AI Inference: {rows_done}/{total} rows ({rate:.1f} rows/s)...")

    elapsed = time.time() - start
    print(f"AI Inference complete: {total} rows in {elapsed:.1f}s ({total / elapsed:.1f} rows/s)")
    return all_labels, all_confs, all_statuses


def split_combined_label(combined, normalize_aliases):
    if pd.isna(combined) or str(combined).strip() == "":
        return "không_có", "không_có", "không_có", "không_có"

    parts = str(combined).split(" | ")
    d_sp = parts[0] if len(parts) > 0 else "không_có"
    loai = parts[1] if len(parts) > 1 else "không_có"
    l1 = parts[2] if len(parts) > 2 else "không_có"
    l2 = parts[3] if len(parts) > 3 else "không_có"
    return normalize_label(d_sp, loai, l1, l2, normalize_aliases)


def compute_accuracy_breakdown(df, label_aliases):
    rows = []
    for _, row in df.iterrows():
        gt_dsp, gt_loai, gt_l1, gt_l2 = normalize_label(
            row.get("Dòng SP", "không_có"),
            row.get("Loại", "không_có"),
            row.get("Lớp 1", "không_có"),
            row.get("Lớp 2", "không_có"),
            label_aliases,
        )
        pd_dsp, pd_loai, pd_l1, pd_l2 = split_combined_label(row.get("predicted_label"), label_aliases)

        rows.append({
            "gt_dong_sp": gt_dsp,
            "gt_loai": gt_loai,
            "gt_lop1": gt_l1,
            "gt_lop2": gt_l2,
            "pd_dong_sp": pd_dsp,
            "pd_loai": pd_loai,
            "pd_lop1": pd_l1,
            "pd_lop2": pd_l2,
        })

    eval_df = pd.DataFrame(rows)
    results = {}
    for level in ["dong_sp", "loai", "lop1", "lop2"]:
        gt_col = f"gt_{level}"
        pd_col = f"pd_{level}"
        correct = (eval_df[gt_col] == eval_df[pd_col]).sum()
        total = len(eval_df)
        results[level] = {"correct": int(correct), "total": total, "accuracy": correct / total if total > 0 else 0.0}

    correct_combined = (
        (eval_df["gt_dong_sp"] == eval_df["pd_dong_sp"])
        & (eval_df["gt_loai"] == eval_df["pd_loai"])
        & (eval_df["gt_lop1"] == eval_df["pd_lop1"])
        & (eval_df["gt_lop2"] == eval_df["pd_lop2"])
    ).sum()
    results["combined"] = {
        "correct": int(correct_combined),
        "total": len(eval_df),
        "accuracy": correct_combined / len(eval_df) if len(eval_df) > 0 else 0.0,
    }

    return results, eval_df


def plot_confusion_heatmap(eval_df, top_n=20):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    combined_gt = eval_df["gt_dong_sp"] + " | " + eval_df["gt_loai"] + " | " + eval_df["gt_lop1"] + " | " + eval_df["gt_lop2"]
    combined_pd = eval_df["pd_dong_sp"] + " | " + eval_df["pd_loai"] + " | " + eval_df["pd_lop1"] + " | " + eval_df["pd_lop2"]

    confusion = pd.crosstab(combined_gt, combined_pd)
    confusion.index.name = "Ground Truth"
    confusion.columns.name = "Predicted"
    if confusion.empty or confusion.size == 0:
        print("Warning: Confusion matrix is empty, skipping heatmap.")
        return pd.DataFrame(columns=["ground_truth", "predicted", "count"])

    errors = confusion.copy()
    for idx, row_label in enumerate(errors.index):
        if row_label in errors.columns:
            col_idx = errors.columns.get_loc(row_label)
            errors.iloc[idx, col_idx] = 0

    error_sums = errors.sum(axis=1) + errors.sum(axis=0)
    top_n_actual = min(top_n, len(error_sums))
    top_series = error_sums.nlargest(top_n_actual)
    common_set = set(top_series.index) & set(confusion.index) & set(confusion.columns)

    if len(common_set) == 0:
        print("Warning: No common indices for top confusion, skipping heatmap.")
        return pd.DataFrame(columns=["ground_truth", "predicted", "count"])

    common_labels = list(common_set)
    top_confusion = confusion.loc[common_labels, common_labels]

    fig_w = max(12, len(common_labels) * 0.6)
    fig_h = max(10, len(common_labels) * 0.5)
    plt.figure(figsize=(fig_w, fig_h))
    sns.heatmap(top_confusion, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5, cbar_kws={"label": "Count"})
    plt.title(f"Confusion Matrix - Top {len(common_labels)} Most Confused Classes", fontsize=14)
    plt.xlabel("Predicted", fontsize=12)
    plt.ylabel("Ground Truth", fontsize=12)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()

    out_path = os.path.join(OUTPUT_DIR, "confusion_matrix_top20.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Confusion matrix heatmap saved to {out_path}")

    confused_pairs = []
    for gt_idx in range(len(errors)):
        for pd_idx in range(len(errors)):
            if gt_idx != pd_idx:
                val = errors.iloc[gt_idx, pd_idx]
                if val > 0:
                    confused_pairs.append({
                        "ground_truth": errors.index[gt_idx],
                        "predicted": errors.columns[pd_idx],
                        "count": int(val),
                    })

    confused_df = pd.DataFrame(confused_pairs)
    if not confused_df.empty:
        confused_df = confused_df.sort_values("count", ascending=False).head(10)
    return confused_df


def compare_dict_vs_ai(df):
    dict_enabled = "dict_label" in df.columns and df["dict_label"].notna().any()

    if not dict_enabled:
        return {"dict_coverage_pct": 0, "dict_accuracy": 0, "ai_accuracy": 0, "overlap": {}}

    label_aliases = {
        "dong_sp": load_label_standard().get("dong_sp", {}).get("aliases", {}),
        "loai": load_label_standard().get("loai", {}).get("aliases", {}),
        "lop1": load_label_standard().get("lop1", {}).get("aliases", {}),
        "lop2": load_label_standard().get("lop2", {}).get("aliases", {}),
    }

    total = len(df)
    dict_handled = df["dict_label"].notna().sum()
    dict_coverage = dict_handled / total * 100 if total > 0 else 0

    dict_correct = 0
    ai_correct = 0
    both_correct = 0
    both_wrong = 0
    dict_only_correct = 0
    ai_only_correct = 0

    for _, row in df.iterrows():
        gt_dsp, gt_loai, gt_l1, gt_l2 = normalize_label(
            row.get("Dòng SP", "không_có"), row.get("Loại", "không_có"),
            row.get("Lớp 1", "không_có"), row.get("Lớp 2", "không_có"), label_aliases,
        )

        dict_right = False
        if pd.notna(row.get("dict_label")):
            dd, dl, d1, d2 = split_combined_label(row["dict_label"], label_aliases)
            if (dd, dl, d1, d2) == (gt_dsp, gt_loai, gt_l1, gt_l2):
                dict_right = True
                dict_correct += 1

        ai_right = False
        if pd.notna(row.get("predicted_label")):
            ad, al, a1, a2 = split_combined_label(row["predicted_label"], label_aliases)
            if (ad, al, a1, a2) == (gt_dsp, gt_loai, gt_l1, gt_l2):
                ai_right = True
                ai_correct += 1

        if dict_right and ai_right:
            both_correct += 1
        elif not dict_right and not ai_right:
            both_wrong += 1
        elif dict_right and not ai_right:
            dict_only_correct += 1
        elif not dict_right and ai_right:
            ai_only_correct += 1

    dict_acc = dict_correct / dict_handled * 100 if dict_handled > 0 else 0
    ai_acc = ai_correct / total * 100 if total > 0 else 0

    return {
        "dict_coverage_pct": round(dict_coverage, 2),
        "dict_handled_rows": int(dict_handled),
        "dict_accuracy": round(dict_acc, 2),
        "dict_correct": int(dict_correct),
        "ai_accuracy": round(ai_acc, 2),
        "ai_correct": int(ai_correct),
        "total_rows": int(total),
        "overlap": {
            "both_correct": int(both_correct),
            "both_wrong": int(both_wrong),
            "dict_only_correct": int(dict_only_correct),
            "ai_only_correct": int(ai_only_correct),
        },
    }


def compute_calibration_curve(df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if "ai_confidence" not in df.columns or df["ai_confidence"].isna().all():
        print("Warning: No AI confidence scores available, skipping calibration curve.")
        return pd.DataFrame(), None

    label_aliases = {
        "dong_sp": load_label_standard().get("dong_sp", {}).get("aliases", {}),
        "loai": load_label_standard().get("loai", {}).get("aliases", {}),
        "lop1": load_label_standard().get("lop1", {}).get("aliases", {}),
        "lop2": load_label_standard().get("lop2", {}).get("aliases", {}),
    }

    bins = [0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
    bin_labels = ["0-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.85", "0.85-0.9", "0.9-0.95", "0.95-1.0"]

    calib_data = []
    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i + 1]
        mask = (df["ai_confidence"] / 100 >= low) & (df["ai_confidence"] / 100 < high)
        if i == len(bins) - 2:
            mask = df["ai_confidence"] / 100 >= low

        bin_df = df[mask]
        count = len(bin_df)
        correct = 0
        if count > 0:
            for _, row in bin_df.iterrows():
                gt_dsp, gt_loai, gt_l1, gt_l2 = normalize_label(
                    row.get("Dòng SP", "không_có"), row.get("Loại", "không_có"),
                    row.get("Lớp 1", "không_có"), row.get("Lớp 2", "không_có"), label_aliases,
                )
                pd_dsp, pd_loai, pd_l1, pd_l2 = split_combined_label(row["predicted_label"], label_aliases)
                if (gt_dsp, gt_loai, gt_l1, gt_l2) == (pd_dsp, pd_loai, pd_l1, pd_l2):
                    correct += 1

        actual_acc = correct / count if count > 0 else 0
        avg_conf = bin_df["ai_confidence"].mean() / 100 if count > 0 else 0
        calib_data.append({
            "bin": bin_labels[i],
            "range": f"[{low}, {high})",
            "count": count,
            "actual_accuracy": round(actual_acc, 4),
            "avg_confidence": round(avg_conf, 4),
        })

    calib_df = pd.DataFrame(calib_data)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    x = np.arange(len(calib_df))
    width = 0.35

    bars1 = ax1.bar(x - width / 2, calib_df["count"], width, label="Sample Count", color="#87CEEB", alpha=0.8)
    ax1.set_xlabel("Confidence Bin")
    ax1.set_ylabel("Sample Count", color="#4682B4")
    ax1.tick_params(axis="y", labelcolor="#4682B4")

    ax2 = ax1.twinx()
    ax2.plot(x, calib_df["actual_accuracy"], "o-", color="#FF6347", linewidth=2, markersize=8, label="Actual Accuracy")
    ax2.plot(x, calib_df["avg_confidence"], "s--", color="#333333", linewidth=2, markersize=8, label="Avg Confidence (diagonal)")
    ax2.set_ylabel("Accuracy / Confidence", color="#FF6347")
    ax2.tick_params(axis="y", labelcolor="#FF6347")
    ax2.set_ylim(0, 1.05)

    ax1.set_xticks(x)
    ax1.set_xticklabels(calib_df["bin"], rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    plt.title("Calibration Curve - Confidence vs Actual Accuracy", fontsize=14)
    plt.tight_layout()

    out_path = os.path.join(OUTPUT_DIR, "calibration_curve.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Calibration curve saved to {out_path}")

    optimal_bin = None
    for _, row in calib_df.iterrows():
        if row["actual_accuracy"] > 0 and row["actual_accuracy"] >= row["avg_confidence"] * 0.9:
            optimal_bin = row["bin"]
        else:
            break

    return calib_df, optimal_bin


def find_optimal_threshold(calib_df):
    sorted_df = calib_df.sort_values("actual_accuracy", ascending=False)
    if not sorted_df.empty:
        top = sorted_df.iloc[0]
        return top["range"], top["actual_accuracy"], top["count"]
    return None, 0, 0


def generate_report(accuracy_results, confused_pairs, dict_vs_ai, calibration_df, optimal_bin,
                    eval_df, test_size, duration, args, data_source, test_text):
    report_path = os.path.join(OUTPUT_DIR, "error_analysis_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("  ERROR ANALYSIS REPORT - Phase 1\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Test data source: {data_source}\n")
        f.write(f"Test rows: {test_size}\n")
        f.write(f"Dict paths: {args.dict_paths if args.dict_paths else 'default'}\n")
        f.write(f"Total time: {duration:.1f}s\n")
        f.write("\n")

        f.write("-" * 50 + "\n")
        f.write("  1. ACCURACY BREAKDOWN\n")
        f.write("-" * 50 + "\n\n")
        f.write(f"{'Level':<22} {'Correct':>10} {'Total':>10} {'Accuracy':>12}\n")
        f.write("-" * 54 + "\n")
        for level in ["dong_sp", "loai", "lop1", "lop2", "combined"]:
            r = accuracy_results[level]
            f.write(f"{level:<22} {r['correct']:>10} {r['total']:>10} {r['accuracy']:>11.2%}\n")

        f.write("\n")
        f.write("-" * 50 + "\n")
        f.write("  2. DICT vs AI COMPARISON\n")
        f.write("-" * 50 + "\n\n")
        for k, v in dict_vs_ai.items():
            if k != "overlap":
                f.write(f"  {k}: {v}\n")
        f.write("\n  Overlap Analysis:\n")
        for k, v in dict_vs_ai.get("overlap", {}).items():
            f.write(f"    {k}: {v}\n")

        f.write("\n")
        f.write("-" * 50 + "\n")
        f.write("  3. TOP CONFUSED CLASS PAIRS\n")
        f.write("-" * 50 + "\n\n")
        if not confused_pairs.empty:
            for _, row in confused_pairs.iterrows():
                f.write(f"  GT: {row['ground_truth']}\n")
                f.write(f"  PD: {row['predicted']}\n")
                f.write(f"  Count: {row['count']}\n\n")
        else:
            f.write("  No confusion data available.\n")

        f.write("\n")
        f.write("-" * 50 + "\n")
        f.write("  4. CALIBRATION CURVE\n")
        f.write("-" * 50 + "\n\n")
        if not calibration_df.empty:
            f.write(calibration_df.to_string(index=False))
        else:
            f.write("  No calibration data available.\n")

        f.write(f"\n\n  Suggested optimal threshold bin: {optimal_bin}\n")

        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("  END OF REPORT\n")
        f.write("=" * 70 + "\n")

    print(f"\nSummary report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 1 Error Analysis")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit test rows (sample from test set)")
    parser.add_argument("--dict-paths", nargs="+", default=None, help="Custom dict paths")
    parser.add_argument("--no-dict", action="store_true", help="Skip dictionary matching")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI inference")
    parser.add_argument("--data", type=str, default=None,
                        help="Alternative data source (xlsx/csv with Tên hàng, Dòng SP, Loại, Lớp 1, Lớp 2)")
    args = parser.parse_args()

    dict_paths = args.dict_paths if args.dict_paths else DEFAULT_DICT_PATHS
    dict_paths = [os.path.join(BASE_DIR, p) if not os.path.isabs(p) else p for p in dict_paths]
    dict_paths = [p for p in dict_paths if os.path.exists(p)]
    if not dict_paths and not args.no_dict:
        print("Warning: No dict files found. Dict matching will be skipped.")
        args.no_dict = True

    start_time = time.time()

    label_standard = load_label_standard()
    label_aliases = {
        "dong_sp": label_standard.get("dong_sp", {}).get("aliases", {}),
        "loai": label_standard.get("loai", {}).get("aliases", {}),
        "lop1": label_standard.get("lop1", {}).get("aliases", {}),
        "lop2": label_standard.get("lop2", {}).get("aliases", {}),
    }

    print("\n" + "=" * 60)
    print("  PHASE 1: ERROR ANALYSIS")
    print("=" * 60 + "\n")

    data_source = args.data if args.data else TRAIN_DATA
    print(f"[1/7] Loading & splitting test data (random_state={RANDOM_STATE})...")
    print(f"  Source: {data_source}")
    test_df = load_and_split_data(data_source, args.max_rows)
    test_size = len(test_df)

    test_text = test_df["text"].iloc[0] if len(test_df) > 0 else ""

    print("\n[2/7] Loading model...")
    tokenizer, model, label_encoder, device = load_model_and_encoder(MODEL_PATH)

    if not args.no_dict:
        print(f"\n[3/7] Running dictionary predictions ({len(dict_paths)} dicts)...")
        print(f"  Dict files: {dict_paths}")
        dict_start = time.time()
        dict_results = run_dict_predictions(test_df, dict_paths)
        for col in dict_results.columns:
            test_df[col] = dict_results[col].values
        print(f"  Dict predictions done in {time.time() - dict_start:.1f}s")

    if not args.no_ai:
        print("\n[4/7] Running AI predictions...")
        ai_labels, ai_confs, ai_statuses = run_ai_predictions(test_df, tokenizer, model, label_encoder, device)
        test_df["ai_label"] = ai_labels
        test_df["ai_confidence"] = ai_confs
        test_df["ai_status"] = ai_statuses
    else:
        test_df["ai_label"] = None
        test_df["ai_confidence"] = np.nan
        test_df["ai_status"] = "N/A"

    if "dict_label" in test_df.columns and not args.no_dict:
        test_df["predicted_label"] = test_df["dict_label"].fillna(
            test_df["ai_label"] if "ai_label" in test_df.columns else None
        )
    elif "ai_label" in test_df.columns:
        test_df["predicted_label"] = test_df["ai_label"]
    else:
        test_df["predicted_label"] = None

    print("\n[5/7] Computing accuracy breakdown...")
    accuracy_results, eval_df = compute_accuracy_breakdown(test_df, label_aliases)
    acc_df = pd.DataFrame([
        {"level": level, "correct": r["correct"], "total": r["total"], "accuracy": f"{r['accuracy']:.4f}"}
        for level, r in accuracy_results.items()
    ])
    acc_path = os.path.join(OUTPUT_DIR, "accuracy_breakdown.csv")
    acc_df.to_csv(acc_path, index=False)
    print(f"Accuracy breakdown saved to {acc_path}")
    print(f"\n  Combined Accuracy: {accuracy_results['combined']['accuracy']:.2%}")
    for level in ["dong_sp", "loai", "lop1", "lop2"]:
        print(f"  {level}: {accuracy_results[level]['accuracy']:.2%}")

    print("\n[6/7] Generating confusion matrix...")
    confused_pairs = plot_confusion_heatmap(eval_df, top_n=20)
    pairs_path = os.path.join(OUTPUT_DIR, "top10_confused_pairs.csv")
    confused_pairs.to_csv(pairs_path, index=False)
    print(f"Top confused pairs saved to {pairs_path}")

    print("\n[7/7] Computing dict vs AI comparison + calibration curve...")
    dict_vs_ai = compare_dict_vs_ai(test_df)
    dvsa_path = os.path.join(OUTPUT_DIR, "dict_vs_ai_report.csv")
    dvsa_row = {k: v for k, v in dict_vs_ai.items() if k != "overlap"}
    for k, v in dict_vs_ai.get("overlap", {}).items():
        dvsa_row[f"overlap_{k}"] = v
    pd.DataFrame([dvsa_row]).to_csv(dvsa_path, index=False)
    print(f"Dict vs AI report saved to {dvsa_path}")

    calibration_df, optimal_bin = compute_calibration_curve(test_df)
    calib_path = os.path.join(OUTPUT_DIR, "calibration_data.csv")
    calibration_df.to_csv(calib_path, index=False)
    print(f"Calibration data saved to {calib_path}")

    duration = time.time() - start_time
    generate_report(accuracy_results, confused_pairs, dict_vs_ai, calibration_df, optimal_bin,
                    eval_df, test_size, duration, args, data_source, test_text)

    print(f"\n{'=' * 60}")
    print(f"  ANALYSIS COMPLETE in {duration:.1f}s")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
