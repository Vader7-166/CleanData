#!/usr/bin/env python3
"""
Phase 5 - Cross Validation: Doi chieu cheo 3 chieu.

Dung DICT_HQ_2026 lam "trong tai" de phat hien loi cua model va nguoc lai.
Chay 3 nguon du doan tren tap test (10%):
1. DICT_HQ_2026 (co bo loc HS code)
2. dictv3
3. PhoBERT AI multitask model

Outputs:
- analysis/output/cross_validation_report.csv
- analysis/output/dict_fixes_needed.csv
- analysis/output/hard_cases.csv
"""

import os
import sys
import time
import json
import re
import pandas as pd
import numpy as np
import warnings
import torch

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.core.dictionary_matcher import DictionaryMatcher
from backend.core.data_cleaner import DataCleaner

MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(BASE_DIR, "working"))
TRAIN_DATA = os.path.join(BASE_DIR, "dataset", "HQ 2025.xlsx")
DICT_HQ_PATH = os.path.join(BASE_DIR, "dataset", "DICT_HQ_2026.csv")
DICT_V3_PATH = os.path.join(BASE_DIR, "dataset", "dictv3.csv")
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


def split_combined_label(combined, normalize_aliases):
    if pd.isna(combined) or str(combined).strip() == "":
        return "không_có", "không_có", "không_có", "không_có"

    parts = str(combined).split(" | ")
    d_sp = parts[0] if len(parts) > 0 else "không_có"
    loai = parts[1] if len(parts) > 1 else "không_có"
    l1 = parts[2] if len(parts) > 2 else "không_có"
    l2 = parts[3] if len(parts) > 3 else "không_có"
    return normalize_label(d_sp, loai, l1, l2, normalize_aliases)


def load_and_split_data(xlsx_path):
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
    return test_df


def main():
    start_time = time.time()
    
    label_standard = load_label_standard()
    label_aliases = {
        "dong_sp": label_standard.get("dong_sp", {}).get("aliases", {}),
        "loai": label_standard.get("loai", {}).get("aliases", {}),
        "lop1": label_standard.get("lop1", {}).get("aliases", {}),
        "lop2": label_standard.get("lop2", {}).get("aliases", {}),
    }

    print("\n" + "=" * 60)
    print("  PHASE 5: 3-WAY CROSS VALIDATION")
    print("=" * 60 + "\n")

    # 1. Load data
    test_df = load_and_split_data(TRAIN_DATA)
    total_test_rows = len(test_df)

    # 2. Load matchers
    print("\nLoading Matchers & Models...")
    if not os.path.exists(DICT_HQ_PATH):
        print(f"Error: Dict HQ not found at {DICT_HQ_PATH}")
        sys.exit(1)
    if not os.path.exists(DICT_V3_PATH):
        print(f"Error: Dict v3 not found at {DICT_V3_PATH}")
        sys.exit(1)

    print("  Initializing DICT_HQ_2026 Matcher (with HS filter support)...")
    matcher_hq = DictionaryMatcher(dict_paths=[DICT_HQ_PATH])

    print("  Initializing dictv3 Matcher...")
    matcher_v3 = DictionaryMatcher(dict_paths=[DICT_V3_PATH])

    print("  Initializing PhoBERT Multitask Model via DataCleaner...")
    cleaner = DataCleaner(MODEL_PATH)

    # 3. Predict
    print("\nRunning predictions...")
    
    # 3.1 Dict HQ
    dict_hq_labels = []
    print("  Running DICT_HQ_2026 predictions...")
    for idx, row in test_df.iterrows():
        label, _, _ = matcher_hq.predict(row['text'], hs_code=row['Mã HS'])
        dict_hq_labels.append(label)
        
    # 3.2 Dict v3
    dict_v3_labels = []
    print("  Running dictv3 predictions...")
    for idx, row in test_df.iterrows():
        label, _, _ = matcher_v3.predict(row['text'])
        dict_v3_labels.append(label)

    # 3.3 AI Model
    print("  Running PhoBERT Multitask AI predictions...")
    ai_results = cleaner.predict_ai_batch(test_df['text'].tolist(), batch_size=64)
    ai_labels = [res[0] for res in ai_results]

    test_df['pred_hq'] = dict_hq_labels
    test_df['pred_v3'] = dict_v3_labels
    test_df['pred_ai'] = ai_labels

    # 4. Alignment & Classification
    print("\nClassifying prediction alignment patterns...")
    
    report_rows = []
    dict_fixes = []
    hard_cases = []

    pattern_counts = {
        "Pattern 1 (Dicts correct, AI wrong)": 0,
        "Pattern 2 (Dict_HQ correct, AI & v3 wrong)": 0,
        "Pattern 3 (AI correct, Dict_HQ & v3 wrong)": 0,
        "Pattern 4 (All 3 wrong)": 0,
        "Pattern 5 (Dict_HQ & AI correct, v3 wrong)": 0,
        "Others (All correct or other agreements)": 0
    }

    for idx, (_, row) in enumerate(test_df.iterrows()):
        # Normalize labels
        gt_dsp, gt_loai, gt_lop1, gt_lop2 = normalize_label(
            row['Dòng SP'], row['Loại'], row['Lớp 1'], row['Lớp 2'], label_aliases
        )
        gt_norm = (gt_dsp, gt_loai, gt_lop1, gt_lop2)

        hq_norm = split_combined_label(row['pred_hq'], label_aliases)
        v3_norm = split_combined_label(row['pred_v3'], label_aliases)
        ai_norm = split_combined_label(row['pred_ai'], label_aliases)

        hq_correct = (hq_norm == gt_norm)
        v3_correct = (v3_norm == gt_norm)
        ai_correct = (ai_norm == gt_norm)

        pattern = "Others (All correct or other agreements)"
        action = "None"
        
        # Classify patterns
        if hq_correct and v3_correct and not ai_correct:
            pattern = "Pattern 1 (Dicts correct, AI wrong)"
            action = "Add sample to AI training set"
            pattern_counts[pattern] += 1
        elif hq_correct and not ai_correct and not v3_correct:
            pattern = "Pattern 2 (Dict_HQ correct, AI & v3 wrong)"
            action = "Dict_HQ superior (promote to primary)"
            pattern_counts[pattern] += 1
        elif not hq_correct and ai_correct and not v3_correct:
            pattern = "Pattern 3 (AI correct, Dict_HQ & v3 wrong)"
            action = "Review and fix DICT_HQ_2026 keywords"
            pattern_counts[pattern] += 1
        elif not hq_correct and not ai_correct and not v3_correct:
            pattern = "Pattern 4 (All 3 wrong)"
            action = "Hard case - Manual review needed"
            pattern_counts[pattern] += 1
        elif hq_correct and ai_correct and not v3_correct:
            pattern = "Pattern 5 (Dict_HQ & AI correct, v3 wrong)"
            action = "Deprecate/Replace corresponding dictv3 entry"
            pattern_counts[pattern] += 1
        else:
            pattern_counts[pattern] += 1

        # Check if there is any mismatch or if any model is incorrect
        has_disagreement = (row['pred_hq'] != row['pred_v3']) or (row['pred_hq'] != row['pred_ai']) or (row['pred_ai'] != row['combined_label'])
        
        gt_str = " | ".join(gt_norm)
        hq_str = " | ".join(hq_norm) if row['pred_hq'] else "không_có"
        v3_str = " | ".join(v3_norm) if row['pred_v3'] else "không_có"
        ai_str = " | ".join(ai_norm)

        # 1. Add to cross validation report if any disagreement or error exists
        if has_disagreement or not hq_correct or not ai_correct or not v3_correct:
            report_rows.append({
                "Tên hàng": row['Tên hàng'],
                "Mã HS": row['Mã HS'],
                "Ground Truth": gt_str,
                "Dict_HQ Pred": hq_str if row['pred_hq'] else "None",
                "dictv3 Pred": v3_str if row['pred_v3'] else "None",
                "AI Pred": ai_str,
                "Pattern": pattern,
                "Action": action
            })

        # 2. Add to dict fixes needed
        if pattern == "Pattern 3 (AI correct, Dict_HQ & v3 wrong)":
            detail = matcher_hq.get_best_match_detail(row['text'], hs_code=row['Mã HS'])
            matched_kw = detail['mapping']['label_str'] if detail else "Unknown"
            dict_fixes.append({
                "Tên hàng": row['Tên hàng'],
                "Mã HS": row['Mã HS'],
                "Matched Dict Label": matched_kw,
                "Wrong Dict Pred": hq_str,
                "Correct AI Pred (GT)": gt_str,
                "Action Required": "Correct or refine keyword rule in DICT_HQ_2026"
            })

        # 3. Add to hard cases
        if pattern == "Pattern 4 (All 3 wrong)":
            hard_cases.append({
                "Tên hàng": row['Tên hàng'],
                "Mã HS": row['Mã HS'],
                "Ground Truth": gt_str,
                "Dict_HQ Pred": hq_str if row['pred_hq'] else "None",
                "dictv3 Pred": v3_str if row['pred_v3'] else "None",
                "AI Pred": ai_str
            })

    # Save reports
    report_path = os.path.join(OUTPUT_DIR, "cross_validation_report.csv")
    pd.DataFrame(report_rows).to_csv(report_path, index=False, encoding='utf-8-sig')
    print(f"\nSaved cross_validation_report.csv to {report_path} ({len(report_rows)} rows)")

    fixes_path = os.path.join(OUTPUT_DIR, "dict_fixes_needed.csv")
    pd.DataFrame(dict_fixes).to_csv(fixes_path, index=False, encoding='utf-8-sig')
    print(f"Saved dict_fixes_needed.csv to {fixes_path} ({len(dict_fixes)} rows)")

    hard_path = os.path.join(OUTPUT_DIR, "hard_cases.csv")
    pd.DataFrame(hard_cases).to_csv(hard_path, index=False, encoding='utf-8-sig')
    print(f"Saved hard_cases.csv to {hard_path} ({len(hard_cases)} rows)")

    # Print summary statistics
    print("\n" + "-" * 50)
    print("  SUMMARY STATISTICS")
    print("-" * 50)
    for pat, count in pattern_counts.items():
        pct = count / total_test_rows * 100
        print(f"  {pat:<45}: {count:>4} ({pct:>5.2f}%)")
    print("-" * 50)

    duration = time.time() - start_time
    print(f"\nCross Validation analysis completed in {duration:.2f} seconds.")


if __name__ == "__main__":
    main()
