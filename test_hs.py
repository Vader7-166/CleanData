import pandas as pd
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

with open('Create_Dictionary/Raw/8539-NK-Th12.2025.xlsx', 'rb') as f:
    raw_nk = load_robust_df(f.read(), '8539-NK-Th12.2025.xlsx')

print(raw_nk['HS_Code'].head(20).tolist())
