import pandas as pd
from backend.core.dict_generator import DictionaryGenerator
import io

def load_robust_df(content, filename):
    is_csv = filename.endswith('.csv')
    if is_csv:
        for enc in ['utf-8', 'latin1', 'utf-8-sig']:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str, skiprows=9)
                if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns:
                    return df
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str)
                if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns:
                    return df
            except Exception:
                continue
        return pd.read_csv(io.BytesIO(content), encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype=str)
    else:
        try:
            df = pd.read_excel(io.BytesIO(content), dtype=str, skiprows=9)
            if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns:
                return df
            return pd.read_excel(io.BytesIO(content), dtype=str)
        except Exception:
            return pd.read_excel(io.BytesIO(content), dtype=str)

# Load raw
with open('Create_Dictionary/Raw/7020-NK-Th12.2025.xlsx', 'rb') as f:
    raw_nk = load_robust_df(f.read(), '7020-NK-Th12.2025.xlsx')
with open('Create_Dictionary/Raw/7020-XK-Th12.2025.xlsx', 'rb') as f:
    raw_xk = load_robust_df(f.read(), '7020-XK-Th12.2025.xlsx')
raw_df = pd.concat([raw_nk, raw_xk], ignore_index=True)

# Load draft
tax_df = pd.read_excel('Create_Dictionary/phan_loai_7020.xlsx', sheet_name='Phân loại')

# Ensure we have the necessary columns for the generator
print("Tax columns:", tax_df.columns)
print("Raw columns:", raw_df.columns)

generator = DictionaryGenerator()
final_df = generator.extract_keywords_for_taxonomy(tax_df, raw_df)

print("\n--- RESULTS ---")
print(final_df[['Mã HS', 'Lớp 2', 'Keyword']].head(20))
