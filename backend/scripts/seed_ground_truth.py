import pandas as pd
import numpy as np
import re
import os
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(script_dir, "../../../Dữ liệu hải quan/Đã xử lý")
DB_PATH = os.path.join(script_dir, "../storage/ground_truth.db")
HQ_FILES = ["HQ 2025.xlsx", "HQ 2026.xlsx"]

def clean_text_basic(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # Loại bỏ ký tự phân cách hải quan "#&" và giữ phần dài nhất
    if '#&' in text:
        parts = text.split('#&')
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            text = max(parts, key=len)
    # Loại bỏ ký tự đặc biệt
    text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
    return ' '.join(text.split()).strip()

def process_file(file_path):
    print(f"Reading {file_path}...")
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return None
    
    required_cols = ['Mã HS', 'Tên hàng', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Missing columns {missing} in {file_path}")
        return None
    
    df = df[required_cols].copy()
    df.dropna(subset=['Tên hàng', 'Lớp 2'], inplace=True)
    
    # Chuẩn hóa Text
    df['clean_text'] = df['Tên hàng'].apply(clean_text_basic)
    df = df[df['clean_text'].str.strip() != '']
    
    # Fill NA for labels
    for col in ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']:
        df[col] = df[col].fillna("").astype(str).str.strip()
        
    df['hs_code'] = df['Mã HS'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    return df

def seed_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    dfs = []
    for file in HQ_FILES:
        path = os.path.join(DATA_DIR, file)
        if os.path.exists(path):
            df = process_file(path)
            if df is not None:
                dfs.append(df)
        else:
            print(f"File not found: {path}")
            
    if not dfs:
        print("No data to process.")
        return
        
    final_df = pd.concat(dfs, ignore_index=True)
    
    # Check for contradictions
    print("Checking for data contradictions...")
    # Group by clean_text and hs_code and see if it maps to multiple Lớp 2
    conflict_check = final_df.groupby(['hs_code', 'clean_text'])['Lớp 2'].nunique()
    conflicts = conflict_check[conflict_check > 1].index.tolist()
    
    if conflicts:
        print(f"Found {len(conflicts)} conflicting texts. Removing them to ensure ground truth purity.")
        # Filter out conflicts
        conflict_df = pd.DataFrame()
        for hs, text in conflicts:
            mask = (final_df['hs_code'] == hs) & (final_df['clean_text'] == text)
            conflict_df = pd.concat([conflict_df, final_df[mask]])
            final_df = final_df[~mask]
            
        conflict_df.to_csv("conflicting_ground_truth.csv", index=False, encoding='utf-8-sig')
        print(f"Saved conflicting rows to conflicting_ground_truth.csv")
    
    # Drop pure duplicates
    final_df = final_df.drop_duplicates(subset=['hs_code', 'clean_text', 'Lớp 2'])
    
    print(f"Final Ground Truth dataset size: {len(final_df)} rows")
    
    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    final_df[['hs_code', 'Tên hàng', 'clean_text', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']].to_sql('ground_truth', conn, if_exists='replace', index=False)
    
    # Create indexes
    conn.execute('CREATE INDEX idx_hs_code ON ground_truth(hs_code)')
    conn.execute('CREATE INDEX idx_lop2 ON ground_truth("Lớp 2")')
    conn.close()
    print("Successfully seeded ground truth database.")

if __name__ == "__main__":
    seed_database()
