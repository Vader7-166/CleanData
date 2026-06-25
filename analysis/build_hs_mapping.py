#!/usr/bin/env python3
"""
Phase 2.5: Build HS Code → Company Label Mapping Table.

Trích xuất từ HQ-2025.xlsx: với mỗi 4-digit HS prefix, thống kê phân phối
Dòng SP, Lớp 1, Lớp 2 phổ biến nhất kèm confidence score.
Output: config/hs_company_mapping.json
"""

import json
import os
import sys
import re
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

DATA_PATH = os.path.join(BASE_DIR, "dataset", "HQ 2025.xlsx")
OUTPUT_PATH = os.path.join(BASE_DIR, "config", "hs_company_mapping.json")
LABEL_STANDARD_PATH = os.path.join(BASE_DIR, "config", "label_standard.json")


def load_label_aliases():
    with open(LABEL_STANDARD_PATH, "r", encoding="utf-8") as f:
        std = json.load(f)
    return {
        "dong_sp": std.get("dong_sp", {}).get("aliases", {}),
        "loai": std.get("loai", {}).get("aliases", {}),
        "lop1": std.get("lop1", {}).get("aliases", {}),
        "lop2": std.get("lop2", {}).get("aliases", {}),
    }


def normalize(val, aliases, level):
    val = str(val).strip()
    if val in ("nan", "None", "0", ""):
        return "không_có"
    val = aliases.get(val, val)
    if level in ("lop1", "lop2"):
        val = val.lower()
    return val


def clean_hs(ma_hs):
    cleaned = re.sub(r'\D', '', str(ma_hs))
    if len(cleaned) >= 4:
        return cleaned
    return None


def main():
    aliases = load_label_aliases()

    print(f"Loading {DATA_PATH}...")
    df = pd.read_excel(DATA_PATH)
    df = df.dropna(subset=['Tên hàng'])
    df = df.fillna('')

    for col in ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']:
        if col not in df.columns:
            df[col] = 'không_có'
        df[col] = df[col].astype(str).replace('', 'không_có')

    df['dong_sp_norm'] = df['Dòng SP'].apply(lambda x: normalize(x, aliases['dong_sp'], 'dong_sp'))
    df['loai_norm'] = df['Loại'].apply(lambda x: normalize(x, aliases['loai'], 'loai'))
    df['lop1_norm'] = df['Lớp 1'].apply(lambda x: normalize(x, aliases['lop1'], 'lop1'))
    df['lop2_norm'] = df['Lớp 2'].apply(lambda x: normalize(x, aliases['lop2'], 'lop2'))
    df['hs_code'] = df['Mã HS'].apply(clean_hs)
    df['hs_prefix'] = df['hs_code'].str[:4]

    df = df[df['hs_code'].notna()]
    print(f"Total rows: {len(df)} | Unique HS codes: {df['hs_code'].nunique()} | Unique prefixes: {df['hs_prefix'].nunique()}")

    label_cols = [("dong_sp", "dong_sp_norm"), ("loai", "loai_norm"),
                  ("lop1", "lop1_norm"), ("lop2", "lop2_norm")]

    def build_entry(sub, total):
        entry = {"total_products": int(total)}
        for level, col in label_cols:
            counts = sub[col].value_counts()
            top_label = counts.index[0]
            top_count = counts.iloc[0]
            confidence = top_count / total

            entry[f"{level}_top"] = top_label
            entry[f"{level}_confidence"] = round(confidence, 4)
            entry[f"{level}_alt"] = counts.index[1] if len(counts) > 1 else None
            entry[f"{level}_alt_confidence"] = round(counts.iloc[1] / total, 4) if len(counts) > 1 else None
        return entry

    print("\n--- 4-Digit Prefix Level ---")
    prefix_mapping = {}
    for prefix in sorted(df['hs_prefix'].unique()):
        sub = df[df['hs_prefix'] == prefix]
        entry = build_entry(sub, len(sub))
        entry["hs_prefix"] = prefix
        prefix_mapping[prefix] = entry

    print("\n--- Full HS Code Level ---")
    hs_mapping = {}
    for hs_code in sorted(df['hs_code'].unique()):
        sub = df[df['hs_code'] == hs_code]
        entry = build_entry(sub, len(sub))
        entry["hs_code"] = hs_code
        hs_mapping[hs_code] = entry

    stats = {"total_hs_codes": len(hs_mapping), "total_prefixes": len(prefix_mapping)}

    high = sum(1 for e in hs_mapping.values()
               if max(e.get(f"{l}_confidence", 0) for l in ["dong_sp", "lop1", "lop2"]) >= 0.8)
    med = sum(1 for e in hs_mapping.values()
              if 0.5 <= max(e.get(f"{l}_confidence", 0) for l in ["dong_sp", "lop1", "lop2"]) < 0.8)
    low = sum(1 for e in hs_mapping.values()
              if max(e.get(f"{l}_confidence", 0) for l in ["dong_sp", "lop1", "lop2"]) < 0.5)
    stats["high_confidence"] = high
    stats["medium_confidence"] = med
    stats["low_confidence"] = low

    output = {"meta": stats, "prefix_level": prefix_mapping, "hs_code_level": hs_mapping}

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nMapping saved to {OUTPUT_PATH}")
    print(f"Prefixes: {stats['total_prefixes']} | HS codes: {stats['total_hs_codes']}")
    print(f"  High confidence (>=80%): {high}")
    print(f"  Medium confidence (50-79%): {med}")
    print(f"  Low confidence (<50%): {low}")

    print("\nPrefix-level mapping:")
    for prefix, entry in prefix_mapping.items():
        print(f"  {prefix} ({entry['total_products']} rows)")
        for level in ["dong_sp", "loai", "lop1", "lop2"]:
            print(f"    {level}: {entry[f'{level}_top']} ({entry[f'{level}_confidence']:.1%})")

    print("\nHS code-level sample (top 10 by products):")
    top_hs = sorted(hs_mapping.items(), key=lambda x: x[1]['total_products'], reverse=True)[:10]
    for hs_code, entry in top_hs:
        print(f"  {hs_code} ({entry['total_products']} rows)")
        for level in ["dong_sp", "lop1", "lop2"]:
            lbl = entry[f"{level}_top"]
            conf = entry[f"{level}_confidence"]
            print(f"    {level}: {lbl} ({conf:.1%})")

    print(f"\nLow confidence HS codes (need manual review):")
    for hs_code, entry in hs_mapping.items():
        max_conf = max(entry.get(f"{l}_confidence", 0) for l in ["dong_sp", "lop1", "lop2"])
        if max_conf < 0.5:
            print(f"  {hs_code} ({entry['total_products']} rows)")
            for level in ["dong_sp", "lop1", "lop2"]:
                lbl = entry[f"{level}_top"]
                conf = entry[f"{level}_confidence"]
                alt = entry.get(f"{level}_alt")
                print(f"    {level}: {lbl} ({conf:.1%}) | alt: {alt}")


if __name__ == "__main__":
    main()
