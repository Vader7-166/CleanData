#!/usr/bin/env python3
"""
verify_pipeline_9405.py - Pipeline kiểm chứng + củng cố dict và model.

Luồng mới:
  1. Load raw file -> map column -> extract info
  2. Dict matching (Aho-Corasick + semantic fallback) trên ALL rows
  3. AI inference (PhoBERT multi-task + SBERT embedding) trên ALL rows
  4. DictEnhancer: phân tích disagreement, sinh đề xuất dict, hard cases, retrain data
  5. Báo cáo kiểm chứng + báo cáo enhancement

Output:
  - analysis/output/9405_XK_predict.csv
  - analysis/output/9405_validation_report.txt
  - analysis/output/9405_spotcheck.txt
  - analysis/output/9405_dict_enhancement_proposals.csv
  - analysis/output/9405_hard_cases.csv
  - analysis/output/9405_train_phase6_augmented.csv
  - analysis/output/9405_dict_enhancement_report.txt
"""

import sys
import os
import json
import time
import re
import gc
import warnings
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.core.dictionary_matcher import DictionaryMatcher
from backend.core.worker import trich_xuat_thong_tin
from analysis.dict_enhancer import DictEnhancer

# ─── CONFIG ──────────────────────────────────────────────────────────────────
RAW_FILE = BASE_DIR / "dataset" / "9405-XK-Th12.2025.xlsx"
HQ_FILE = BASE_DIR / "dataset" / "HQ 2025.xlsx"
MAPPING_FILE = BASE_DIR / "config" / "hs_company_mapping.json"
DICT_FILES = [
    str(BASE_DIR / "dataset" / "DICT_HQ_2026_v2.csv"),
    str(BASE_DIR / "dataset" / "dictv3.csv"),
]
MODEL_PATH = str(BASE_DIR / "working")
OUTPUT_DIR = BASE_DIR / "analysis" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PREDICT_CSV = OUTPUT_DIR / "9405_XK_predict.csv"
REPORT_TXT = OUTPUT_DIR / "9405_validation_report.txt"
SPOTCHECK_TXT = OUTPUT_DIR / "9405_spotcheck.txt"
PREFIX = "9405_"


# ─── PHASE 1: LOAD & EXTRACT ─────────────────────────────────────────────────

def load_raw_file(path):
    print(f"\n{'='*60}")
    print(f"PHASE 1: Loading raw file: {path}")
    print(f"{'='*60}")

    df = pd.read_excel(path, header=9)
    print(f"  Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"  Rows: {len(df)}")

    assert 'HS_Code' in df.columns, "Missing HS_Code column!"
    assert 'Detailed_Product' in df.columns, "Missing Detailed_Product column!"

    hs_codes = df['HS_Code'].dropna().unique()
    print(f"  Unique HS codes: {len(hs_codes)}")
    return df


def extract_info(df_raw):
    print(f"\n  Extracting info from {len(df_raw)} rows...")
    extracted = df_raw['Detailed_Product'].apply(
        lambda x: pd.Series(trich_xuat_thong_tin(x))
    )
    extracted.columns = ['Hang', 'CongSuat', 'TenHang']

    input_for_ai = (
        "Hang: " + extracted['Hang'].astype(str)
        + " - Cong suat: " + extracted['CongSuat'].astype(str)
        + " - San pham: " + extracted['TenHang'].astype(str).str.lower()
    )
    return extracted, input_for_ai


# ─── PHASE 2: DICT MATCHING (ALL ROWS) ───────────────────────────────────────

def run_dict(dict_paths, input_for_ai, hs_series):
    print(f"\n{'='*60}")
    print(f"PHASE 2: Dict matching (with semantic fallback)")
    print(f"{'='*60}")

    print(f"  Initializing DictionaryMatcher with {len(dict_paths)} dicts...")
    matcher = DictionaryMatcher(dict_paths=dict_paths)

    print(f"  Batch-running dict matching on {len(input_for_ai)} rows...")
    pred_results = matcher.predict_batch(
        input_for_ai.tolist(),
        hs_codes=hs_series.tolist(),
    )

    ac_match = 0
    sem_match = 0
    fail = 0
    results = []

    for idx, (label_str, conf, status) in enumerate(pred_results):
        source = 'none'
        if label_str is not None:
            if 'Ngữ nghĩa' in status or 'Ngua nghia' in status:
                source = 'dict_semantic'
                sem_match += 1
            else:
                source = 'dict'
                ac_match += 1
        else:
            fail += 1

        results.append({
            'idx': idx,
            'input_for_ai': input_for_ai.iloc[idx],
            'HS_Code': hs_series.iloc[idx],
            'dict_label': label_str,
            'dict_conf': conf if label_str is not None else 0.0,
            'dict_status': status if label_str is not None else "Can kiem tra",
            'dict_source': source,
        })

    n = len(input_for_ai)
    print(f"  AC match:    {ac_match:>6,} ({100*ac_match/n:>5.1f}%)")
    print(f"  Semantic:    {sem_match:>6,} ({100*sem_match/n:>5.1f}%)")
    print(f"  Fail:        {fail:>6,} ({100*fail/n:>5.1f}%)")
    print(f"  Total:       {ac_match + sem_match + fail:>6,}")

    return pd.DataFrame(results), matcher


# ─── PHASE 3: AI INFERENCE (ALL ROWS) ────────────────────────────────────────

def run_ai(model_path, input_for_ai, batch_size=64):
    print(f"\n{'='*60}")
    print(f"PHASE 3: AI inference on ALL rows")
    print(f"{'='*60}")

    os.environ["MODEL_PATH"] = model_path
    from backend.core.data_cleaner import DataCleaner
    cleaner = DataCleaner(model_path)

    n = len(input_for_ai)
    print(f"  Running AI inference on {n} rows (batch_size={batch_size})...")

    ai_results = cleaner.predict_ai_batch(input_for_ai.tolist(), batch_size=batch_size)

    auto_count = 0
    check_count = 0
    records = []
    for idx, (label, conf, status) in enumerate(ai_results):
        records.append({
            'ai_label': label,
            'ai_conf': conf,
            'ai_status': status,
        })
        if status == "Tu dong duyet (AI)" or status == "Tự động duyệt (AI)":
            auto_count += 1
        else:
            check_count += 1

    print(f"  AI auto-accept: {auto_count}/{n} ({100*auto_count/n:.1f}%)")
    print(f"  AI needs review: {check_count}/{n} ({100*check_count/n:.1f}%)")

    ai_df = pd.DataFrame(records)

    try:
        print(f"  Computing embeddings for {n} texts...")
        embs = cleaner.get_embedding(input_for_ai.tolist())
        ai_df['embedding'] = [e.tolist() if isinstance(e, np.ndarray) else e for e in embs] if embs is not None else None
    except Exception as e:
        print(f"  Embedding skipped: {e}")
        ai_df['embedding'] = None

    del cleaner
    gc.collect()

    return ai_df


# ─── PHASE 4: MERGE & ENHANCE ───────────────────────────────────────────────

def merge_and_enhance(df_raw, dict_df, ai_df, input_for_ai):
    print(f"\n{'='*60}")
    print(f"PHASE 4: Merge + Dict Enhancement")
    print(f"{'='*60}")

    records = []
    for idx in range(len(df_raw)):
        dr = dict_df.iloc[idx]
        ar = ai_df.iloc[idx]

        if dr['dict_label'] is not None:
            final_label = dr['dict_label']
            final_conf = dr['dict_conf']
            final_status = dr['dict_status']
            source = dr['dict_source']
        elif ar['ai_label'] is not None:
            final_label = ar['ai_label']
            final_conf = ar['ai_conf']
            final_status = ar['ai_status']
            source = 'ai'
        else:
            final_label = None
            final_conf = 0.0
            final_status = "Can kiem tra"
            source = 'none'

        if final_label is None or (isinstance(final_label, float) and pd.isna(final_label)):
            parts = ['không_có'] * 5
        else:
            parts = str(final_label).split(' | ')
        while len(parts) < 5:
            parts.append('không_có')

        records.append({
            'index': idx,
            'Detailed_Product': df_raw.iloc[idx].get('Detailed_Product', ''),
            'Detailed_Product_EN': df_raw.iloc[idx].get('Detailed_Product_EN', ''),
            'HS_Code': str(df_raw.iloc[idx].get('HS_Code', '')),
            'source': source,
            'Dong_SP': parts[0],
            'Loai': parts[1],
            'Lop1': parts[2],
            'Lop2': parts[3],
            'Du_doan_HS': parts[4],
            'Confidence': final_conf,
            'Status': final_status,
            'Quantity': df_raw.iloc[idx].get('Quantity', 0),
            'Total_Value_USD': df_raw.iloc[idx].get('Total_Value_USD', 0),
            'dict_label': dr['dict_label'],
            'dict_conf': dr['dict_conf'],
            'dict_status': dr['dict_status'],
            'ai_label': ar['ai_label'],
            'ai_conf': ar['ai_conf'],
            'ai_status': ar['ai_status'],
        })

    df_result = pd.DataFrame(records)

    print(f"\n  Final label distribution:")
    print(f"  Dict (AC):    {(df_result['source'] == 'dict').sum():>6,}")
    print(f"  Dict (Sem):   {(df_result['source'] == 'dict_semantic').sum():>6,}")
    print(f"  AI:           {(df_result['source'] == 'ai').sum():>6,}")
    print(f"  None:         {(df_result['source'] == 'none').sum():>6,}")

    df_result.to_csv(PREDICT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n  Predictions saved to: {PREDICT_CSV}")

    return df_result


def run_enhancement(df_raw, df_result, input_for_ai):
    print(f"\n{'='*60}")
    print(f"PHASE 4b: DictEnhancer analysis")
    print(f"{'='*60}")

    from backend.core.data_cleaner import DataCleaner

    get_embedding_fn = None
    try:
        tmp_cleaner = DataCleaner(MODEL_PATH)
        get_embedding_fn = tmp_cleaner.get_embedding
    except Exception as e:
        print(f"  WARNING: Cannot load model for embeddings: {e}")
        print(f"  WARNING: Semantic dedup will be disabled.")

    enhancer = DictEnhancer(
        get_embedding_fn=get_embedding_fn,
        output_dir=str(OUTPUT_DIR),
    )

    disagreement_df = enhancer.classify_disagreements(
        df_result,
        dict_label_col="dict_label",
        ai_label_col="ai_label",
        ai_conf_col="ai_conf",
    )

    prop_df = enhancer.propose_dict_keywords(disagreement_df, df_result)
    hard_df = enhancer.generate_hard_cases(disagreement_df)
    train_df = enhancer.generate_training_data(disagreement_df, df_result)

    enhancer.export_suggestions(prop_df, hard_df, train_df, prefix=PREFIX)
    enhancer.generate_report(disagreement_df, prop_df, hard_df, train_df, prefix=PREFIX)

    if get_embedding_fn is not None:
        del tmp_cleaner
        gc.collect()

    return disagreement_df, prop_df, hard_df, train_df


# ─── PHASE 5: REPORTS ────────────────────────────────────────────────────────

def generate_validation_report(df_pred):
    print(f"\n{'='*60}")
    print(f"PHASE 5: Generating validation report")
    print(f"{'='*60}")

    n_total = len(df_pred)
    n_dict = (df_pred['source'] == 'dict').sum()
    n_dict_sem = (df_pred['source'] == 'dict_semantic').sum()
    n_ai = (df_pred['source'] == 'ai').sum()
    n_none = (df_pred['source'] == 'none').sum()
    n_auto = (df_pred['Status'].fillna('').str.contains('Tu dong duyet|Tự động duyệt', na=False)).sum()
    n_check = n_total - n_auto

    total_value = df_pred['Total_Value_USD'].sum()
    total_qty = df_pred['Quantity'].sum()
    n_with_hs = df_pred['HS_Code'].notna().sum()
    unique_hs = df_pred['HS_Code'].dropna().nunique()

    dong_sp_dist = df_pred['Dong_SP'].value_counts()
    loai_dist = df_pred['Loai'].value_counts()
    lop1_top = df_pred['Lop1'].value_counts().head(15)
    lop2_top = df_pred['Lop2'].value_counts().head(15)
    source_status = pd.crosstab(df_pred['source'], df_pred['Status'])

    lines = []
    lines.append("=" * 70)
    lines.append("BAO CAO KIEM CHUNG PIPELINE DICT -> MODEL")
    lines.append(f"File: 9405-XK-Th12.2025.xlsx")
    lines.append(f"Thoi gian: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    lines.append(f"\n1. TONG QUAN")
    lines.append(f"   Tong so dong: {n_total:,}")
    lines.append(f"   Tong gia tri (USD): {total_value:,.2f}")
    lines.append(f"   Tong so luong: {total_qty:,.0f}")
    lines.append(f"   So dong co Ma HS: {n_with_hs:,} ({100*n_with_hs/n_total:.1f}%)")
    lines.append(f"   So Ma HS duy nhat: {unique_hs}")

    lines.append(f"\n2. PHAN PHOI NGUON XU LY")
    lines.append(f"   Dict (AC):         {n_dict:>6,} ({100*n_dict/n_total:>5.1f}%)")
    lines.append(f"   Dict (Semantic):   {n_dict_sem:>6,} ({100*n_dict_sem/n_total:>5.1f}%)")
    lines.append(f"   AI:                {n_ai:>6,} ({100*n_ai/n_total:>5.1f}%)")
    lines.append(f"   Khong xu ly:       {n_none:>6,} ({100*n_none/n_total:>5.1f}%)")
    lines.append(f"   ---")
    lines.append(f"   Tu dong duyet:     {n_auto:>6,} ({100*n_auto/n_total:>5.1f}%)")
    lines.append(f"   Can kiem tra:      {n_check:>6,} ({100*n_check/n_total:>5.1f}%)")

    lines.append(f"\n3. PHAN PHOI DONG SP")
    for label, cnt in dong_sp_dist.items():
        lines.append(f"   {label:<25s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n4. PHAN PHOI LOAI")
    for label, cnt in loai_dist.items():
        lines.append(f"   {label:<10s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n5. TOP 15 LOP 1")
    for label, cnt in lop1_top.items():
        lines.append(f"   {label:<30s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n6. TOP 15 LOP 2")
    for label, cnt in lop2_top.items():
        lines.append(f"   {label:<30s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n7. NGUON vs TRANG THAI")
    for src in source_status.index:
        for st in source_status.columns:
            val = source_status.loc[src, st]
            if val > 0:
                lines.append(f"   {src:<15s} -> {st:<35s}: {val:>6,}")

    lines.append(f"\n8. SEMANTIC FALLBACK IMPACT")
    if n_dict_sem > 0:
        lines.append(f"   Dict coverage increased by {n_dict_sem} rows ({100*n_dict_sem/n_total:.1f}%)")
        lines.append(f"   vs previous pipeline would have fallen back to AI")
    else:
        lines.append(f"   No semantic fallback matches (SBERT unavailable or all matched by AC)")

    lines.append(f"\n9. ENHANCEMENT OUTPUTS")
    for fname in ['dict_enhancement_proposals.csv', 'hard_cases.csv', 'train_phase6_augmented.csv']:
        fpath = OUTPUT_DIR / f"{PREFIX}{fname}"
        if fpath.exists():
            lines.append(f"   {fname}: saved")
        else:
            lines.append(f"   {fname}: not generated (no applicable cases)")

    lines.append(f"\n{'='*70}")
    lines.append("HET BAO CAO")
    lines.append(f"{'='*70}")

    report_text = '\n'.join(lines)
    with open(REPORT_TXT, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(report_text)
    print(f"\n  Report saved to: {REPORT_TXT}")
    return report_text


def generate_spotcheck(df_pred, n_dict=10, n_dict_sem=10, n_ai=10, n_check=5):
    print(f"\n  Generating spot-check file...")

    samples = []
    groups = []

    d_count = (df_pred['source'] == 'dict').sum()
    if d_count > 0:
        groups.append(("DICT (AC)", df_pred[df_pred['source'] == 'dict'].sample(min(n_dict, d_count))))

    ds_count = (df_pred['source'] == 'dict_semantic').sum()
    if ds_count > 0:
        groups.append(("DICT (SEMANTIC)", df_pred[df_pred['source'] == 'dict_semantic'].sample(min(n_dict_sem, ds_count))))

    ai_count = (df_pred['source'] == 'ai').sum()
    if ai_count > 0:
        groups.append(("AI", df_pred[df_pred['source'] == 'ai'].sample(min(n_ai, ai_count))))

    check_df = df_pred[df_pred['Status'] == 'Can kiem tra']
    if len(check_df) > 0:
        groups.append(("CAN KIEM TRA", check_df.sample(min(n_check, len(check_df)))))

    lines = []
    lines.append("=" * 70)
    lines.append("SPOT-CHECK: MAU KIEM TRA THU CONG")
    lines.append(f"Thoi gian: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    for title, subset in groups:
        lines.append(f"\n{'-'*70}")
        lines.append(f"  {title} ({len(subset)} samples)")
        lines.append(f"{'-'*70}")
        for idx, (_, row) in enumerate(subset.iterrows()):
            lines.append(f"\n  Sample #{idx+1}")
            lines.append(f"  HS_Code:       {row['HS_Code']}")
            lines.append(f"  Product:       {str(row['Detailed_Product'])[:150]}")
            lines.append(f"  Product_EN:    {str(row.get('Detailed_Product_EN', ''))[:100]}")
            lines.append(f"  Source:        {row['source']}")
            lines.append(f"  Dong SP:       {row['Dong_SP']}")
            lines.append(f"  Loai:          {row['Loai']}")
            lines.append(f"  Lop 1:         {row['Lop1']}")
            lines.append(f"  Lop 2:         {row['Lop2']}")
            lines.append(f"  Confidence:    {row['Confidence']}")
            lines.append(f"  Status:        {row['Status']}")

    lines.append(f"\n{'='*70}")
    lines.append("HET SPOT-CHECK")
    lines.append(f"{'='*70}")

    spot_text = '\n'.join(lines)
    with open(SPOTCHECK_TXT, 'w', encoding='utf-8') as f:
        f.write(spot_text)
    print(f"  Spot-check saved to: {SPOTCHECK_TXT}")
    return spot_text


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    start_time = time.time()

    df_raw = load_raw_file(RAW_FILE)
    extracted, input_for_ai = extract_info(df_raw)
    hs_series = df_raw['HS_Code'].fillna('').astype(str)

    dict_df, matcher = run_dict(DICT_FILES, input_for_ai, hs_series)

    ai_df = run_ai(MODEL_PATH, input_for_ai)

    df_result = merge_and_enhance(df_raw, dict_df, ai_df, input_for_ai)

    disagreement_df, prop_df, hard_df, train_df = run_enhancement(df_raw, df_result, input_for_ai)

    generate_validation_report(df_result)
    generate_spotcheck(df_result)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"TOTAL TIME: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"{'='*60}")

    print(f"\n--- Enhancement Summary ---")
    if prop_df is not None and len(prop_df) > 0:
        print(f"  Dict proposals: {len(prop_df)} (review at: {OUTPUT_DIR / f'{PREFIX}dict_enhancement_proposals.csv'})")
    if hard_df is not None and len(hard_df) > 0:
        print(f"  Hard cases: {len(hard_df)} (review at: {OUTPUT_DIR / f'{PREFIX}hard_cases.csv'})")
    if train_df is not None and len(train_df) > 0:
        print(f"  Retrain samples: {len(train_df)} (at: {OUTPUT_DIR / f'{PREFIX}train_phase6_augmented.csv'})")


if __name__ == '__main__':
    main()
