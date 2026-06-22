#!/usr/bin/env python3
"""
verify_pipeline_9405.py - Kiểm chứng luồng xử lý dict -> model
trên file 9405-XK-Th12.2025.xlsx (xuất khẩu).

Luồng:
  1. Load raw file -> map column -> dict matching (Aho-Corasick)
  2. AI fallback (PhoBERT multi-task) cho rows dict không match
  3. Validate bằng hs_company_mapping.json + cross-ref HQ 2025
  4. Spot-check thủ công

Output:
  - analysis/output/9405_XK_predict.csv
  - analysis/output/9405_validation_report.txt
  - analysis/output/9405_spotcheck.txt
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

# Add project root to path for backend imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.core.dictionary_matcher import DictionaryMatcher
from backend.core.worker import trich_xuat_thong_tin

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


# ─── PHASE 1: LOAD & RUN PIPELINE ─────────────────────────────────────────────

def load_raw_file(path):
    """Load 9405-XK Excel file (header=9 for bigtradedata format)."""
    print(f"\n{'='*60}")
    print(f"PHASE 1: Loading raw file: {path}")
    print(f"{'='*60}")

    df = pd.read_excel(path, header=9)
    print(f"  Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"  Rows: {len(df)}")

    # Verify key columns exist
    assert 'HS_Code' in df.columns, "Missing HS_Code column!"
    assert 'Detailed_Product' in df.columns, "Missing Detailed_Product column!"

    # Count unique HS codes
    hs_codes = df['HS_Code'].dropna().unique()
    print(f"  Unique HS codes: {len(hs_codes)}")
    print(f"  Sample HS codes: {sorted(hs_codes)[:10]}")

    return df


def run_pipeline(df_raw, dict_paths):
    """Run dict matching + AI fallback on all rows."""
    print(f"\n  Initializing DictionaryMatcher with {len(dict_paths)} dicts...")
    matcher = DictionaryMatcher(dict_paths=dict_paths)

    # ── Step 1: Extract info + build input_for_ai ──
    print(f"  Extracting info from {len(df_raw)} rows...")
    extracted = df_raw['Detailed_Product'].apply(
        lambda x: pd.Series(trich_xuat_thong_tin(x))
    )
    extracted.columns = ['Hang', 'CongSuat', 'TenHang']

    input_for_ai = (
        "Hang: " + extracted['Hang'].astype(str)
        + " - Cong suat: " + extracted['CongSuat'].astype(str)
        + " - San pham: " + extracted['TenHang'].astype(str).str.lower()
    )
    input_for_ai = input_for_ai.apply(matcher.clean_text_for_dict)

    # ── Step 2: Dict matching ──
    print(f"  Running dict matching on {len(df_raw)} rows (HS-filtered)...")
    hs_series = df_raw['HS_Code'].fillna('').astype(str)

    dict_results = []
    dict_match_count = 0
    dict_fail_indices = []
    dict_fail_texts = []

    for idx in range(len(df_raw)):
        text = input_for_ai.iloc[idx]
        hs = hs_series.iloc[idx] if hs_series.iloc[idx] else None
        label_str, conf, status = matcher.predict(text, hs_code=hs)

        dict_results.append({
            'idx': idx,
            'input_for_ai': text,
            'HS_Code': hs_series.iloc[idx],
            'dict_label': label_str,
            'dict_conf': conf,
            'dict_status': status,
        })

        if label_str is not None:
            dict_match_count += 1
        else:
            dict_fail_indices.append(idx)
            dict_fail_texts.append(text)

    print(f"  Dict match: {dict_match_count}/{len(df_raw)} "
          f"({100 * dict_match_count / len(df_raw):.1f}%)")
    print(f"  Dict fail: {len(dict_fail_indices)} "
          f"({100 * len(dict_fail_indices) / len(df_raw):.1f}%)")

    # ── Step 3: AI fallback ──
    ai_results = {}  # idx -> (label, conf, status)

    if dict_fail_texts:
        print(f"\n  Loading AI model for {len(dict_fail_texts)} fallback rows...")
        print(f"  Model path: {MODEL_PATH}")

        os.environ["MODEL_PATH"] = MODEL_PATH
        from backend.core.data_cleaner import DataCleaner
        cleaner = DataCleaner(MODEL_PATH)

        # Process in batches for progress tracking
        ai_batch_size = 64
        n_fail = len(dict_fail_texts)
        print(f"  Running AI inference on {n_fail} rows (batch_size={ai_batch_size})...")

        ai_auto_count = 0
        ai_check_count = 0

        for i in range(0, n_fail, ai_batch_size):
            batch_texts = dict_fail_texts[i:i + ai_batch_size]
            batch_indices = dict_fail_indices[i:i + ai_batch_size]

            batch_results = cleaner.predict_ai_batch(batch_texts, batch_size=ai_batch_size)

            for idx_in_batch, (label, conf, status) in zip(batch_indices, batch_results):
                ai_results[idx_in_batch] = (label, conf, status)
                if status == "Tự động duyệt (AI)":
                    ai_auto_count += 1
                else:
                    ai_check_count += 1

            if (i // ai_batch_size) % 20 == 0 or i + ai_batch_size >= n_fail:
                print(f"    AI progress: {min(i + ai_batch_size, n_fail)}/{n_fail} "
                      f"({100 * min(i + ai_batch_size, n_fail) / n_fail:.0f}%)")

        print(f"  AI auto-accept: {ai_auto_count}, Needs review: {ai_check_count}")

        # Clean up to free memory
        del cleaner
        gc.collect()

    # ── Step 4: Merge results ──
    print(f"\n  Merging results...")
    records = []
    for idx in range(len(df_raw)):
        dr = dict_results[idx]
        hs = dr['HS_Code']

        if dr['dict_label'] is not None:
            final_label = dr['dict_label']
            final_conf = dr['dict_conf']
            final_status = dr['dict_status']
            source = 'dict'
        elif idx in ai_results:
            final_label, final_conf, final_status = ai_results[idx]
            source = 'ai'
        else:
            final_label = None
            final_conf = 0.0
            final_status = "Can kiem tra"
            source = 'none'

        # Parse the label (Dong SP | Loai | Lop 1 | Lop 2 | Ma HS)
        parts = final_label.split(' | ') if final_label else ['khong_co'] * 5
        while len(parts) < 5:
            parts.append('khong_co')

        records.append({
            'index': idx,
            'Detailed_Product': df_raw.iloc[idx].get('Detailed_Product', ''),
            'Detailed_Product_EN': df_raw.iloc[idx].get('Detailed_Product_EN', ''),
            'HS_Code': hs,
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
        })

    df_result = pd.DataFrame(records)
    print(f"  Result columns: {list(df_result.columns)}")
    return df_result


# ─── PHASE 2: VALIDATE ─────────────────────────────────────────────────────────

def validate_with_hs_mapping(df_pred, mapping_path):
    """Validate predictions against hs_company_mapping.json."""
    print(f"\n{'='*60}")
    print(f"PHASE 2a: Validate vs hs_company_mapping.json")
    print(f"{'='*60}")

    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    hs_level = mapping.get('hs_code_level', {})
    prefix_level = mapping.get('prefix_level', {})

    # Stats counters
    stats = {
        'total': 0,
        'dong_sp_match_top': 0,
        'dong_sp_match_alt': 0,
        'dong_sp_mismatch': 0,
        'loai_match_top': 0,
        'loai_mismatch': 0,
        'lop1_match_top': 0,
        'lop1_mismatch': 0,
        'lop2_match_top': 0,
        'lop2_mismatch': 0,
        'hs_not_in_mapping': 0,
    }

    mismatch_rows = []

    for idx, row in df_pred.iterrows():
        hs = str(row['HS_Code']).strip()
        if not hs or hs == 'nan':
            continue

        stats['total'] += 1

        # Try full HS code first, then 4-digit prefix
        hs_entry = hs_level.get(hs)
        prefix = hs[:4] if len(hs) >= 4 else None
        pref_entry = prefix_level.get(prefix) if prefix else None

        entry = hs_entry or pref_entry

        if entry is None:
            stats['hs_not_in_mapping'] += 1
            continue

        # Check Dong SP
        dong_sp_top = str(entry.get('dong_sp_top', '')).strip()
        dong_sp_alt = str(entry.get('dong_sp_alt', '') or '').strip()
        pred_dong = str(row['Dong_SP']).strip()

        if pred_dong == dong_sp_top:
            stats['dong_sp_match_top'] += 1
        elif dong_sp_alt and pred_dong == dong_sp_alt:
            stats['dong_sp_match_alt'] += 1
        else:
            stats['dong_sp_mismatch'] += 1

        # Check Loai
        loai_top = str(entry.get('loai_top', '')).strip()
        pred_loai = str(row['Loai']).strip()
        if pred_loai == loai_top:
            stats['loai_match_top'] += 1
        else:
            stats['loai_mismatch'] += 1

        # Check Lop 1
        lop1_top = str(entry.get('lop1_top', '')).strip()
        pred_lop1 = str(row['Lop1']).strip()
        if pred_lop1 == lop1_top:
            stats['lop1_match_top'] += 1
        else:
            stats['lop1_mismatch'] += 1

        # Check Lop 2
        lop2_top = str(entry.get('lop2_top', '')).strip()
        pred_lop2 = str(row['Lop2']).strip()
        if pred_lop2 == lop2_top:
            stats['lop2_match_top'] += 1
        else:
            stats['lop2_mismatch'] += 1

        # Record mismatch details for reporting
        if pred_dong != dong_sp_top:
            mismatch_rows.append({
                'index': idx,
                'HS_Code': hs,
                'Detailed_Product': row['Detailed_Product'][:100],
                'pred_Dong_SP': pred_dong,
                'expected_Dong_SP': dong_sp_top,
                'pred_Loai': pred_loai,
                'pred_Lop1': pred_lop1,
                'pred_Lop2': pred_lop2,
            })

    # Print report
    total = stats['total']
    if total == 0:
        print("  No rows with HS codes found in mapping. Skipping.")
        return stats, mismatch_rows

    print(f"\n  Rows with HS in mapping: {total}")
    print(f"  HS not in mapping: {stats['hs_not_in_mapping']}")

    dong_ok = stats['dong_sp_match_top'] + stats['dong_sp_match_alt']
    print(f"\n  --- Dong SP Validation ---")
    print(f"  Match top: {stats['dong_sp_match_top']} "
          f"({100 * stats['dong_sp_match_top'] / total:.1f}%)")
    print(f"  Match alt: {stats['dong_sp_match_alt']} "
          f"({100 * stats['dong_sp_match_alt'] / total:.1f}%)")
    print(f"  Mismatch:  {stats['dong_sp_mismatch']} "
          f"({100 * stats['dong_sp_mismatch'] / total:.1f}%)")

    print(f"\n  --- Loai Validation ---")
    print(f"  Match top: {stats['loai_match_top']} "
          f"({100 * stats['loai_match_top'] / total:.1f}%)")
    print(f"  Mismatch:  {stats['loai_mismatch']} "
          f"({100 * stats['loai_mismatch'] / total:.1f}%)")

    print(f"\n  --- Lop 1 Validation ---")
    print(f"  Match top: {stats['lop1_match_top']} "
          f"({100 * stats['lop1_match_top'] / total:.1f}%)")
    print(f"  Mismatch:  {stats['lop1_mismatch']} "
          f"({100 * stats['lop1_mismatch'] / total:.1f}%)")

    print(f"\n  --- Lop 2 Validation ---")
    print(f"  Match top: {stats['lop2_match_top']} "
          f"({100 * stats['lop2_match_top'] / total:.1f}%)")
    print(f"  Mismatch:  {stats['lop2_mismatch']} "
          f"({100 * stats['lop2_mismatch'] / total:.1f}%)")

    # Top mismatches
    if mismatch_rows:
        mismatch_df = pd.DataFrame(mismatch_rows)
        top_mismatch = mismatch_df['expected_Dong_SP'].value_counts().head(10)
        print(f"\n  Top 10 expected Dong SP with mismatches:")
        for label, cnt in top_mismatch.items():
            print(f"    {label}: {cnt}")

    return stats, mismatch_rows


def crossref_hq2025(df_pred, hq_path):
    """Cross-reference predictions with HQ 2025 label distributions."""
    print(f"\n{'='*60}")
    print(f"PHASE 2b: Cross-reference vs HQ 2025")
    print(f"{'='*60}")

    print(f"  Loading HQ 2025 (only needed columns)...")
    # Exact column names from Excel (with Vietnamese diacritics)
    df_hq = pd.read_excel(
        hq_path,
        usecols=['Mã HS', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2'],
        dtype={'Mã HS': str}
    )
    df_hq.columns = ['HS_Code', 'Dong_SP', 'Loai', 'Lop1', 'Lop2']
    print(f"  HQ 2025 rows: {len(df_hq)}")

    # Filter to 9405 prefix
    df_hq['HS_prefix'] = df_hq['HS_Code'].astype(str).str[:4]
    df_hq_9405 = df_hq[df_hq['HS_prefix'] == '9405'].copy()
    print(f"  HQ 2025 rows with 9405 prefix: {len(df_hq_9405)}")

    # Get HS codes present in both
    pred_hs_codes = set(df_pred['HS_Code'].dropna().unique())
    hq_hs_codes = set(df_hq_9405['HS_Code'].dropna().unique())
    common_hs = pred_hs_codes & hq_hs_codes
    print(f"  HS codes in predictions: {len(pred_hs_codes)}")
    print(f"  HS codes in HQ 2025 (9405): {len(hq_hs_codes)}")
    print(f"  Common HS codes: {len(common_hs)}")

    if not common_hs:
        print("  No common HS codes to compare. Skipping cross-reference.")
        return {}

    # Build HQ 2025 distribution per HS code
    print(f"  Building HQ 2025 distributions per HS code...")
    hq_dist = {}
    for hs in common_hs:
        subset = df_hq_9405[df_hq_9405['HS_Code'] == hs]
        hq_dist[hs] = {
            'count': len(subset),
            'dong_sp_dist': subset['Dong_SP'].value_counts(normalize=True).to_dict(),
            'loai_dist': subset['Loai'].value_counts(normalize=True).to_dict(),
            'lop1_dist': subset['Lop1'].value_counts(normalize=True).to_dict(),
            'lop2_dist': subset['Lop2'].value_counts(normalize=True).to_dict(),
        }

    # Compare predictions with HQ distributions
    comparison = {}
    for hs in common_hs:
        pred_subset = df_pred[df_pred['HS_Code'] == hs]
        hq_info = hq_dist[hs]

        # Compute predicted distribution
        pred_dong_dist = pred_subset['Dong_SP'].value_counts(normalize=True).to_dict()
        pred_loai_dist = pred_subset['Loai'].value_counts(normalize=True).to_dict()
        pred_lop1_dist = pred_subset['Lop1'].value_counts(normalize=True).to_dict()

        # Compare Dong SP top
        hq_top_dong = max(hq_info['dong_sp_dist'], key=hq_info['dong_sp_dist'].get)
        pred_top_dong = max(pred_dong_dist, key=pred_dong_dist.get) if pred_dong_dist else '?'

        # Compare Loai top
        hq_top_loai = max(hq_info['loai_dist'], key=hq_info['loai_dist'].get)
        pred_top_loai = max(pred_loai_dist, key=pred_loai_dist.get) if pred_loai_dist else '?'

        # Compare Lop 1 top
        hq_top_lop1 = max(hq_info['lop1_dist'], key=hq_info['lop1_dist'].get)
        pred_top_lop1 = max(pred_lop1_dist, key=pred_lop1_dist.get) if pred_lop1_dist else '?'

        # Dong SP distribution similarity (overlap coefficient)
        dong_overlap = sum(
            min(hq_info['dong_sp_dist'].get(k, 0), pred_dong_dist.get(k, 0))
            for k in set(list(hq_info['dong_sp_dist'].keys()) + list(pred_dong_dist.keys()))
        )

        comparison[hs] = {
            'n_hq': hq_info['count'],
            'n_pred': len(pred_subset),
            'hq_top_dong': hq_top_dong,
            'pred_top_dong': pred_top_dong,
            'dong_sp_overlap': dong_overlap,
            'hq_top_loai': hq_top_loai,
            'pred_top_loai': pred_top_loai,
            'hq_top_lop1': hq_top_lop1,
            'pred_top_lop1': pred_top_lop1,
        }

    # Summary stats
    dong_agree = sum(
        1 for c in comparison.values()
        if c['hq_top_dong'] == c['pred_top_dong']
    )
    loai_agree = sum(
        1 for c in comparison.values()
        if c['hq_top_loai'] == c['pred_top_loai']
    )
    lop1_agree = sum(
        1 for c in comparison.values()
        if c['hq_top_lop1'] == c['pred_top_lop1']
    )

    n_common = len(common_hs)
    print(f"\n  Top-1 label agreement between predict and HQ 2025:")
    print(f"    Dong SP: {dong_agree}/{n_common} "
          f"({100 * dong_agree / n_common:.1f}%)")
    print(f"    Loai:    {loai_agree}/{n_common} "
          f"({100 * loai_agree / n_common:.1f}%)")
    print(f"    Lop 1:   {lop1_agree}/{n_common} "
          f"({100 * lop1_agree / n_common:.1f}%)")

    avg_overlap = np.mean([c['dong_sp_overlap'] for c in comparison.values()])
    print(f"\n  Average Dong SP distribution overlap: {avg_overlap:.3f}")

    # Flag HS codes with low overlap
    low_overlap = [
        (hs, c) for hs, c in comparison.items()
        if c['dong_sp_overlap'] < 0.5 and c['n_pred'] >= 5
    ]
    low_overlap.sort(key=lambda x: x[1]['dong_sp_overlap'])

    if low_overlap:
        print(f"\n  HS codes with Dong SP overlap < 0.5 (n_pred >= 5):")
        for hs, c in low_overlap[:10]:
            print(f"    {hs}: overlap={c['dong_sp_overlap']:.2f}, "
                  f"HQ top={c['hq_top_dong']}, Pred top={c['pred_top_dong']}, "
                  f"n_HQ={c['n_hq']}, n_pred={c['n_pred']}")

    return comparison


def generate_report(df_pred, mapping_stats, mapping_mismatches, hq_comparison):
    """Generate comprehensive validation report."""
    print(f"\n{'='*60}")
    print(f"PHASE 3: Generating report")
    print(f"{'='*60}")

    n_total = len(df_pred)
    n_dict = (df_pred['source'] == 'dict').sum()
    n_ai = (df_pred['source'] == 'ai').sum()
    n_none = (df_pred['source'] == 'none').sum()
    n_auto = (df_pred['Status'].fillna('').str.contains('Tự động duyệt', na=False)).sum()
    n_check = (df_pred['Status'].fillna('').str.contains('Cần kiểm tra', na=False)).sum() + n_none

    # HS code coverage
    n_with_hs = df_pred['HS_Code'].notna().sum()
    unique_hs = df_pred['HS_Code'].dropna().nunique()

    # Value distribution
    total_value = df_pred['Total_Value_USD'].sum()
    total_qty = df_pred['Quantity'].sum()

    # Label distribution
    dong_sp_dist = df_pred['Dong_SP'].value_counts()
    loai_dist = df_pred['Loai'].value_counts()
    lop1_top = df_pred['Lop1'].value_counts().head(15)
    lop2_top = df_pred['Lop2'].value_counts().head(15)

    # Source vs Status cross-tab
    source_status = pd.crosstab(df_pred['source'], df_pred['Status'])

    lines = []
    lines.append("=" * 70)
    lines.append("BÁO CÁO KIỂM CHỨNG PIPELINE DICT -> MODEL")
    lines.append(f"File: 9405-XK-Th12.2025.xlsx")
    lines.append(f"Thời gian: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    lines.append(f"\n1. TỔNG QUAN")
    lines.append(f"   Tổng số dòng: {n_total:,}")
    lines.append(f"   Tổng giá trị (USD): {total_value:,.2f}")
    lines.append(f"   Tổng số lượng: {total_qty:,.0f}")
    lines.append(f"   Số dòng có Mã HS: {n_with_hs:,} ({100*n_with_hs/n_total:.1f}%)")
    lines.append(f"   Số Mã HS duy nhất: {unique_hs}")

    lines.append(f"\n2. PHÂN PHỐI NGUỒN XỬ LÝ")
    lines.append(f"   Dict match:     {n_dict:>6,} ({100*n_dict/n_total:>5.1f}%)")
    lines.append(f"   AI fallback:    {n_ai:>6,} ({100*n_ai/n_total:>5.1f}%)")
    lines.append(f"   Không xử lý:    {n_none:>6,} ({100*n_none/n_total:>5.1f}%)")
    lines.append(f"   ---")
    lines.append(f"   Tự động duyệt:  {n_auto:>6,} ({100*n_auto/n_total:>5.1f}%)")
    lines.append(f"   Cần kiểm tra:   {n_check:>6,} ({100*n_check/n_total:>5.1f}%)")

    lines.append(f"\n3. PHÂN PHỐI DÒNG SP")
    for label, cnt in dong_sp_dist.items():
        lines.append(f"   {label:<25s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n4. PHÂN PHỐI LOẠI")
    for label, cnt in loai_dist.items():
        lines.append(f"   {label:<10s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n5. TOP 15 LỚP 1")
    for label, cnt in lop1_top.items():
        lines.append(f"   {label:<30s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n6. TOP 15 LỚP 2")
    for label, cnt in lop2_top.items():
        lines.append(f"   {label:<30s}: {cnt:>6,} ({100*cnt/n_total:>5.1f}%)")

    lines.append(f"\n7. NGUỒN vs TRẠNG THÁI")
    for src in source_status.index:
        for st in source_status.columns:
            val = source_status.loc[src, st]
            if val > 0:
                lines.append(f"   {src:<12s} -> {st:<35s}: {val:>6,}")

    # ── HS Mapping Validation Summary ──
    if mapping_stats and mapping_stats['total'] > 0:
        total_m = mapping_stats['total']
        lines.append(f"\n8. KIỂM TRA VỚI HS COMPANY MAPPING")
        lines.append(f"   Số dòng có HS trong mapping: {total_m:,}")

        dong_ok = mapping_stats['dong_sp_match_top'] + mapping_stats['dong_sp_match_alt']
        lines.append(f"   Dòng SP match (top+alt): {dong_ok:,} "
                     f"({100*dong_ok/total_m:.1f}%)")
        lines.append(f"   Dòng SP mismatch:         "
                     f"{mapping_stats['dong_sp_mismatch']:,} "
                     f"({100*mapping_stats['dong_sp_mismatch']/total_m:.1f}%)")

        loai_ok = mapping_stats['loai_match_top']
        lines.append(f"   Loại match (top):         {loai_ok:,} "
                     f"({100*loai_ok/total_m:.1f}%)")

        lop1_ok = mapping_stats['lop1_match_top']
        lines.append(f"   Lớp 1 match (top):        {lop1_ok:,} "
                     f"({100*lop1_ok/total_m:.1f}%)")

        lop2_ok = mapping_stats['lop2_match_top']
        lines.append(f"   Lớp 2 match (top):        {lop2_ok:,} "
                     f"({100*lop2_ok/total_m:.1f}%)")

        # Top mismatch details
        if mapping_mismatches:
            mm_df = pd.DataFrame(mapping_mismatches)
            top_mm = mm_df['expected_Dong_SP'].value_counts().head(5)
            lines.append(f"\n   Top 5 Dòng SP expected có nhiều mismatch nhất:")
            for label, cnt in top_mm.items():
                lines.append(f"     {label}: {cnt} dòng")

    # ── HQ 2025 Cross-reference ──
    if hq_comparison:
        n_common = len(hq_comparison)
        dong_agree = sum(
            1 for c in hq_comparison.values()
            if c['hq_top_dong'] == c['pred_top_dong']
        )
        loai_agree = sum(
            1 for c in hq_comparison.values()
            if c['hq_top_loai'] == c['pred_top_loai']
        )
        lop1_agree = sum(
            1 for c in hq_comparison.values()
            if c['hq_top_lop1'] == c['pred_top_lop1']
        )

        lines.append(f"\n9. CROSS-REFERENCE VS HQ 2025")
        lines.append(f"   Số HS code chung: {n_common}")
        lines.append(f"   Top-1 Dòng SP agreement: {dong_agree}/{n_common} "
                     f"({100*dong_agree/n_common:.1f}%)")
        lines.append(f"   Top-1 Loại agreement:    {loai_agree}/{n_common} "
                     f"({100*loai_agree/n_common:.1f}%)")
        lines.append(f"   Top-1 Lớp 1 agreement:   {lop1_agree}/{n_common} "
                     f"({100*lop1_agree/n_common:.1f}%)")

        low_overlap = [
            (hs, c) for hs, c in hq_comparison.items()
            if c['dong_sp_overlap'] < 0.5 and c['n_pred'] >= 5
        ]
        low_overlap.sort(key=lambda x: x[1]['dong_sp_overlap'])
        if low_overlap:
            lines.append(f"\n   HS codes có phân phối Dòng SP khác HQ 2025 (n>=5):")
            for hs, c in low_overlap[:5]:
                overlap_pct = c['dong_sp_overlap'] * 100
                lines.append(f"     {hs}: overlap={overlap_pct:.0f}%, "
                             f"HQ={c['hq_top_dong']}, Pred={c['pred_top_dong']}, "
                             f"n_HQ={c['n_hq']}, n_pred={c['n_pred']}")

    lines.append(f"\n{'='*70}")
    lines.append("HẾT BÁO CÁO")
    lines.append(f"{'='*70}")

    report_text = '\n'.join(lines)

    with open(REPORT_TXT, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"\n  Report saved to: {REPORT_TXT}")
    return report_text


def generate_spotcheck(df_pred, n_dict=15, n_ai=15, n_check=5):
    """Generate spot-check file for manual review."""
    print(f"\n  Generating spot-check file...")

    df_dict = df_pred[df_pred['source'] == 'dict'].sample(min(n_dict, (df_pred['source'] == 'dict').sum()))
    df_ai = df_pred[df_pred['source'] == 'ai'].sample(min(n_ai, (df_pred['source'] == 'ai').sum()))
    df_check = df_pred[df_pred['Status'] == 'Can kiem tra'].sample(
        min(n_check, (df_pred['Status'] == 'Can kiem tra').sum())
    )

    lines = []
    lines.append("=" * 70)
    lines.append("SPOT-CHECK: MẪU KIỂM TRA THỦ CÔNG")
    lines.append(f"Thời gian: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    for title, subset in [("DICT MATCH", df_dict), ("AI PREDICT", df_ai), ("CAN KIEM TRA", df_check)]:
        lines.append(f"\n{'─'*70}")
        lines.append(f"  {title} ({len(subset)} samples)")
        lines.append(f"{'─'*70}")

        for idx, (_, row) in enumerate(subset.iterrows()):
            lines.append(f"\n  Sample #{idx+1}")
            lines.append(f"  HS_Code:       {row['HS_Code']}")
            lines.append(f"  Product:       {str(row['Detailed_Product'])[:150]}")
            lines.append(f"  Product_EN:    {str(row['Detailed_Product_EN'])[:100]}")
            lines.append(f"  Source:        {row['source']}")
            lines.append(f"  Dong SP:       {row['Dong_SP']}")
            lines.append(f"  Loai:          {row['Loai']}")
            lines.append(f"  Lop 1:         {row['Lop1']}")
            lines.append(f"  Lop 2:         {row['Lop2']}")
            lines.append(f"  Confidence:    {row['Confidence']}")
            lines.append(f"  Status:        {row['Status']}")

    lines.append(f"\n{'='*70}")
    lines.append("HẾT SPOT-CHECK")
    lines.append(f"{'='*70}")

    spot_text = '\n'.join(lines)

    with open(SPOTCHECK_TXT, 'w', encoding='utf-8') as f:
        f.write(spot_text)

    print(f"  Spot-check saved to: {SPOTCHECK_TXT}")
    return spot_text


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    start_time = time.time()

    # Phase 1: Load and run pipeline
    df_raw = load_raw_file(RAW_FILE)

    # Run full dataset
    # df_raw = df_raw.head(1000)

    df_pred = run_pipeline(df_raw, DICT_FILES)

    # Save intermediate results
    df_pred.to_csv(PREDICT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n  Predictions saved to: {PREDICT_CSV}")

    # Phase 2: Validate
    mapping_stats, mapping_mismatches = validate_with_hs_mapping(df_pred, MAPPING_FILE)
    hq_comparison = crossref_hq2025(df_pred, HQ_FILE)

    # Phase 3: Report
    generate_report(df_pred, mapping_stats, mapping_mismatches, hq_comparison)
    generate_spotcheck(df_pred)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"TOTAL TIME: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
