import os
import re
import json
import math
import pandas as pd
import numpy as np

# 2.1 Import libraries and setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_PATH = os.path.join(BASE_DIR, "dataset", "DICT_HQ_2026_v2.csv")
MAPPING_PATH = os.path.join(BASE_DIR, "config", "hs_company_mapping.json")
STANDARD_PATH = os.path.join(BASE_DIR, "config", "label_standard.json")
TRAIN_PATH = os.path.join(BASE_DIR, "dataset", "HQ 2025.xlsx")
SYNTHETIC_OUT_PATH = os.path.join(BASE_DIR, "dataset", "synthetic_train_v2.csv")
AUGMENTED_OUT_PATH = os.path.join(BASE_DIR, "dataset", "train_augmented.csv")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
    return ' '.join(text.split()).strip()

def load_label_standard():
    with open(STANDARD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_label(d_sp, lo, l1, l2, std_cfg):
    d_sp = str(d_sp).strip()
    lo = str(lo).strip()
    l1 = str(l1).strip()
    l2 = str(l2).strip()

    # Apply aliases
    d_sp = std_cfg.get("dong_sp", {}).get("aliases", {}).get(d_sp, d_sp)
    lo = std_cfg.get("loai", {}).get("aliases", {}).get(lo, lo)
    l1 = std_cfg.get("lop1", {}).get("aliases", {}).get(l1, l1.lower())
    l2 = std_cfg.get("lop2", {}).get("aliases", {}).get(l2, l2.lower())

    # Replace empty/nan
    d_sp = d_sp if d_sp not in ['nan', 'None', '0', ''] else 'không_có'
    lo = lo if lo not in ['nan', 'None', '0', ''] else 'không_có'
    l1 = l1 if l1 not in ['nan', 'None', '0', ''] else 'không_có'
    l2 = l2 if l2 not in ['nan', 'None', '0', ''] else 'không_có'

    return d_sp, lo, l1, l2

def main():
    # 2.2 Load mapping and standard configurations
    print("Loading mapping and standard configurations...")
    if not os.path.exists(MAPPING_PATH):
        raise FileNotFoundError(f"Mapping file not found: {MAPPING_PATH}")
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        hs_mapping = json.load(f)
        
    std_cfg = load_label_standard()

    # Load regenerated clean dictionary
    print(f"Loading clean dictionary from {DICT_PATH}...")
    if not os.path.exists(DICT_PATH):
        raise FileNotFoundError(f"Dictionary file not found: {DICT_PATH}")
    dict_df = pd.read_csv(DICT_PATH)
    print(f"Loaded dict size: {dict_df.shape}")

    # Generate synthetic training samples
    synthetic_samples = []

    print("Generating synthetic training samples...")
    for idx, row in dict_df.iterrows():
        kw_str = str(row['Keyword']).strip()
        if not kw_str or kw_str == '0':
            continue

        # 2.3 Split keywords (comma-separated, strip whitespace, keep if word count >= 2)
        kws = [k.strip() for k in kw_str.split(',') if k.strip()]
        valid_kws = [k for k in kws if len(k.split()) >= 2]
        
        if not valid_kws:
            continue

        # 2.4 Label and HS cross-validation/override
        hs_code = str(row['Mã HS']).strip()
        dong_sp = str(row['Dòng SP']).strip()
        loai = str(row['Loại']).strip()
        lop1 = str(row['Lớp 1']).strip()
        lop2 = str(row['Lớp 2']).strip()

        # Check mapping for Dòng SP override
        if hs_code in hs_mapping.get('hs_code_level', {}):
            mapping_entry = hs_mapping['hs_code_level'][hs_code]
            if mapping_entry.get('dong_sp_confidence', 0) >= 0.8:
                dong_sp = mapping_entry.get('dong_sp_top', dong_sp)
                
        # Normalize the labels
        dong_sp, loai, lop1, lop2 = normalize_label(dong_sp, loai, lop1, lop2, std_cfg)
        combined_label = f"{dong_sp} | {loai} | {lop1} | {lop2}"

        # 2.5 Calculate sample weights using log(1 + Số lượng SP)
        qty = float(row['Số lượng SP']) if pd.notna(row['Số lượng SP']) else 1.0
        weight = math.log(1 + qty)

        for kw in valid_kws:
            # 2.6 Format synthetic text as "Hãng: không_có - Sản phẩm: {keyword}"
            raw_synthetic_text = f"Hãng: không_có - Sản phẩm: {kw}"
            clean_synthetic_text = clean_text(raw_synthetic_text)
            
            synthetic_samples.append({
                'text': clean_synthetic_text,
                'Dòng SP': dong_sp,
                'Loại': loai,
                'Lớp 1': lop1,
                'Lớp 2': lop2,
                'combined_label': combined_label,
                'weight': weight
            })

    # 2.7 Create DataFrame and save synthetic dataset
    synthetic_df = pd.DataFrame(synthetic_samples)
    print(f"Generated {len(synthetic_df)} synthetic samples.")
    synthetic_df.to_csv(SYNTHETIC_OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"Saved synthetic dataset to {SYNTHETIC_OUT_PATH}")

    # 2.8 Load and preprocess original training data (HQ-2025)
    print(f"Loading original training data from {TRAIN_PATH}...")
    if not os.path.exists(TRAIN_PATH):
        raise FileNotFoundError(f"Original training file not found: {TRAIN_PATH}")
    train_df = pd.read_excel(TRAIN_PATH)
    print(f"Original data size: {train_df.shape}")

    # Standardize columns and normalize labels
    train_df = train_df.dropna(subset=['Tên hàng'])
    train_df = train_df.fillna('')

    cols_to_predict = ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']
    for col in cols_to_predict:
        if col not in train_df.columns:
            train_df[col] = 'không_có'
        else:
            train_df[col] = train_df[col].astype(str).str.strip()

    # Normalize labels in original training data
    print("Normalizing labels in original training dataset...")
    norm_labels = train_df.apply(
        lambda r: normalize_label(r['Dòng SP'], r['Loại'], r['Lớp 1'], r['Lớp 2'], std_cfg),
        axis=1
    )
    train_df['Dòng SP'] = [n[0] for n in norm_labels]
    train_df['Loại'] = [n[1] for n in norm_labels]
    train_df['Lớp 1'] = [n[2] for n in norm_labels]
    train_df['Lớp 2'] = [n[3] for n in norm_labels]

    train_df['combined_label'] = (
        train_df['Dòng SP'] + " | " + train_df['Loại'] + " | " + train_df['Lớp 1'] + " | " + train_df['Lớp 2']
    )

    # Format text for original training data
    train_df['text'] = "Hãng: " + train_df['Hãng'].astype(str) + " - Công suất: " + train_df['Công suất'].astype(str) + " - Sản phẩm: " + train_df['Tên hàng'].astype(str)
    train_df['text'] = train_df['text'].apply(clean_text)
    train_df = train_df[train_df['text'] != '']

    # Set default weight for original samples to 1.0
    train_df['weight'] = 1.0

    # Keep only target columns
    train_keep_cols = ['text', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'combined_label', 'weight']
    train_df_clean = train_df[train_keep_cols].copy()

    # 2.9 Merge and deduplicate on the 'text' column, keeping the original samples
    print("Merging datasets and running deduplication...")
    # Place original dataset first so keep='first' retains original samples
    merged_df = pd.concat([train_df_clean, synthetic_df], ignore_index=True)
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['text'], keep='first')
    after_dedup = len(merged_df)
    
    print(f"Merged count before deduplication: {before_dedup}")
    print(f"Merged count after deduplication: {after_dedup} (Removed {before_dedup - after_dedup} duplicates)")

    # Save augmented dataset
    merged_df.to_csv(AUGMENTED_OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"Saved augmented dataset to {AUGMENTED_OUT_PATH}")
    print("All steps completed successfully!")

if __name__ == "__main__":
    main()
