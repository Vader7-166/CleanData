import sys
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.models import Base, HSCustomsReference

def import_hs_dataset(excel_path, db_url="sqlite:///app.db"):
    if not os.path.exists(excel_path):
        print(f"Error: File not found at {excel_path}")
        return

    print(f"Loading {excel_path}...")
    try:
        # Depending on the actual structure of the Excel file, these column names might need adjustment.
        # Assuming typical customs structure: 'Mã HS', 'Mô tả hàng hóa', 'Cấp độ'
        df = pd.read_excel(excel_path, dtype=str)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Clear existing data
    db.query(HSCustomsReference).delete()
    db.commit()

    print("Populating database...")
    records = []
    
    # Try to identify standard column names or fall back to indices
    # We look for "HS" or "Mã", and "Tên" or "Mô tả"
    hs_col = next((c for c in df.columns if 'hs' in c.lower() or 'mã' in c.lower()), df.columns[0])
    desc_col = next((c for c in df.columns if 'tên' in c.lower() or 'mô tả' in c.lower() or 'hàng hóa' in c.lower()), df.columns[1])
    
    for _, row in df.iterrows():
        hs_code = str(row.get(hs_col, '')).replace('.', '').strip()
        description = str(row.get(desc_col, '')).strip()
        
        if not hs_code or hs_code.lower() == 'nan':
            continue
            
        records.append(HSCustomsReference(
            hs_code=hs_code,
            level=len(hs_code),
            description_vn=description
        ))

    # Bulk save
    try:
        db.bulk_save_objects(records)
        db.commit()
        print(f"Successfully imported {len(records)} HS codes into the database.")
    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dataset", "vn_customs_hs_codes.xlsx")
    excel_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    import_hs_dataset(excel_path)
