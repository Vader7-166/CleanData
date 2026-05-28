"""
One-time migration script: Scan existing dictionary CSV files 
and populate hs_code_prefixes field with unique 4-digit HS prefixes.
"""
import os
import sys
import pandas as pd

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend import database, models

DICTIONARY_STORAGE_PATH = "backend/storage/dictionaries"

def migrate():
    db = database.SessionLocal()
    try:
        dictionaries = db.query(models.Dictionary).all()
        updated = 0
        
        for d in dictionaries:
            if d.hs_code_prefixes:
                print(f"  Skip {d.filename}: already has hs_code_prefixes = {d.hs_code_prefixes}")
                continue
            
            file_path = os.path.join(DICTIONARY_STORAGE_PATH, d.filename)
            if not os.path.exists(file_path):
                print(f"  Skip {d.filename}: file not found at {file_path}")
                continue
            
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig', usecols=['Mã HS'])
            except Exception:
                try:
                    df = pd.read_csv(file_path, encoding='latin1', usecols=['Mã HS'])
                except Exception as e:
                    print(f"  Skip {d.filename}: cannot read - {e}")
                    continue
            
            # Extract unique 4-digit prefixes
            hs_codes = df['Mã HS'].dropna().astype(str)
            prefixes = set()
            for code in hs_codes:
                clean = ''.join(c for c in code if c.isdigit())
                if len(clean) >= 4:
                    prefixes.add(clean[:4])
            
            if prefixes:
                d.hs_code_prefixes = ','.join(sorted(prefixes))
                updated += 1
                print(f"  Updated {d.filename}: hs_code_prefixes = {d.hs_code_prefixes}")
            else:
                print(f"  Skip {d.filename}: no valid HS codes found")
        
        db.commit()
        print(f"\nMigration complete. Updated {updated}/{len(dictionaries)} dictionaries.")
    finally:
        db.close()

if __name__ == "__main__":
    print("Migrating dictionary HS code prefixes...")
    migrate()
