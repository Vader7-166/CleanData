import os
import pandas as pd
import json

def generate_official_taxonomy():
    excel_path = "../../BIEU THUE XNK 2026.04.05.xlsx"
    if not os.path.exists(excel_path):
        excel_path = "BIEU THUE XNK 2026.04.05.xlsx"
        if not os.path.exists(excel_path):
            print("Error: Could not find BIEU THUE XNK 2026.04.05.xlsx")
            return

    print("Loading BIEU THUE XNK...")
    df = pd.read_excel(excel_path, sheet_name='BT2026', skiprows=8, dtype=str)
    
    taxonomy_dict = {}
    
    for _, row in df.iterrows():
        # Column 5 is HS Code, Column 6 is Description
        hs_code = str(row.iloc[5]).strip().replace('.', '')
        desc = str(row.iloc[6]).strip()
        
        if not hs_code or hs_code.lower() == 'nan' or not desc or desc.lower() == 'nan':
            continue
            
        # Clean up description (remove leading hyphens " - - - ")
        desc = desc.lstrip(' -').strip()
        
        # Only store if it's longer than 4 digits (to be used for Lớp 1)
        if len(hs_code) >= 6:
            taxonomy_dict[hs_code] = desc

    # Ensure output dir exists
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    
    out_path = os.path.join(out_dir, "official_hs_taxonomy.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(taxonomy_dict, f, ensure_ascii=False, indent=2)
        
    print(f"Generated official taxonomy with {len(taxonomy_dict)} entries at {out_path}")

if __name__ == "__main__":
    generate_official_taxonomy()
