"""
Seed the HSTaxonomy table with data from the hardcoded dictionaries
in dict_generator.py. Run once to populate the database.

Usage:
    python -m backend.core.seed_taxonomy
"""
import sys
import os

# Ensure the project root is on sys.path when run as a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database import SessionLocal, engine
from backend import models
from backend.core.dict_generator import HS_TAXONOMY, DONG_SP_MAP, HS_TYPE_MAP

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        existing_count = db.query(models.HSTaxonomy).count()
        if existing_count > 0:
            print(f"HSTaxonomy table already has {existing_count} records. Skipping seed.")
            print("Use --force flag to re-seed (will delete existing records).")
            if '--force' not in sys.argv:
                return
            print("Force flag detected. Deleting existing records...")
            db.query(models.HSTaxonomy).delete()
            db.commit()

        inserted = 0
        for hs_code, industry_name in HS_TAXONOMY.items():
            # Determine dong_sp from the 4-digit prefix
            prefix_4 = hs_code[:4]
            dong_sp = DONG_SP_MAP.get(prefix_4, f'SP {prefix_4}')
            
            # Determine default_type from HS_TYPE_MAP
            default_type = HS_TYPE_MAP.get(hs_code, 'NC')

            record = models.HSTaxonomy(
                hs_code_prefix=hs_code,
                dong_sp=dong_sp,
                industry_name=industry_name,
                default_type=default_type,
                source='system'
            )
            db.add(record)
            inserted += 1

        db.commit()
        print(f"Successfully seeded {inserted} records into HSTaxonomy table.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding HSTaxonomy: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed()
