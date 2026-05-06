from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel

from sse_starlette.sse import EventSourceResponse
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
import shutil
import pandas as pd
import numpy as np
import os
import uuid
import asyncio
import time
import io
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .core.data_cleaner import get_cleaner
from .core.dict_generator import DictionaryGenerator
from . import models, auth, database
from .database import engine

PROCESSED_STORAGE_PATH = "backend/storage/processed"
DICTIONARY_STORAGE_PATH = "backend/storage/dictionaries"
os.makedirs(PROCESSED_STORAGE_PATH, exist_ok=True)
os.makedirs(DICTIONARY_STORAGE_PATH, exist_ok=True)

from sqlalchemy import text
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE dictionaries ADD COLUMN is_active BOOLEAN DEFAULT FALSE"))
except Exception as e:
    pass

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Data Cleaning API with Progress & Preview")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs = {}

@app.on_event("startup")
def startup_event():
    print("Loading model on startup...")
    get_cleaner()
    print("Model loaded.")

def get_user_from_token_query(token: str = Query(...), db: Session = Depends(database.get_db)):
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

def cleanup_old_files(user_id: int, db: Session):
    user_jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.user_id == user_id).order_by(models.ProcessingJob.created_at.desc()).all()
    if len(user_jobs) > 10:
        jobs_to_delete = user_jobs[10:]
        for j in jobs_to_delete:
            out_path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{j.id}_{j.filename}")
            remove_file(out_path)
            db.delete(j)
            if j.id in jobs:
                del jobs[j.id]
        db.commit()

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not file.filename.endswith(('.csv', '.xlsx')):
         raise HTTPException(status_code=400, detail="Invalid file format.")
         
    active_dict = db.query(models.Dictionary).filter(models.Dictionary.is_active == True).first()
    if not active_dict:
        raise HTTPException(
            status_code=400, 
            detail="Không có bộ từ điển nào được kích hoạt. Vui lòng upload và chọn một bộ từ điển trước khi Clean Data."
        )
    
    # Retention policy handles cleanup automatically, no block needed here.
    user_jobs_count = db.query(models.ProcessingJob).filter(models.ProcessingJob.user_id == current_user.id).count()

    job_id = str(uuid.uuid4())
    temp_path = f"temp_{job_id}_{file.filename}"
    
    new_job = models.ProcessingJob(id=job_id, filename=file.filename, status="processing", user_id=current_user.id)
    db.add(new_job)
    db.commit()
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    jobs[job_id] = {
        "status": "processing",
        "file_path": None,
        "preview": None,
        "error": None,
        "event_queue": asyncio.Queue()
    }
    
    asyncio.create_task(process_job(job_id, temp_path, file.filename))
    return {"job_id": job_id, "message": "Upload successful, processing started."}

async def process_job(job_id: str, temp_path: str, original_filename: str):
    job = jobs.get(job_id)
    if not job:
        return
        
    async def progress_callback(msg):
        await job["event_queue"].put({"event": "progress", "data": msg})

    try:
        start_time = time.time()
        await progress_callback("Loading Data...")
        is_csv = original_filename.endswith('.csv')
        
        def load_dataframe(path, csv_mode):
            if csv_mode:
                for enc in ['utf-8', 'latin1']:
                    try:
                        df = pd.read_csv(path, encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str, skiprows=9)
                        if 'HS_Code' in df.columns or 'VN_Exporter' in df.columns or 'VN_Importer' in df.columns:
                            return df
                        
                        df = pd.read_csv(path, encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str)
                        return df
                    except Exception:
                        continue
                return pd.read_csv(path, encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype=str)
            else:
                try:
                    df = pd.read_excel(path, dtype=str, skiprows=9)
                    if 'HS_Code' in df.columns or 'VN_Exporter' in df.columns or 'VN_Importer' in df.columns:
                        return df
                    return pd.read_excel(path, dtype=str)
                except Exception:
                    return pd.read_excel(path, dtype=str)

        df = await asyncio.to_thread(load_dataframe, temp_path, is_csv)
            
        db_sync = database.SessionLocal()
        active_dict = db_sync.query(models.Dictionary).filter(models.Dictionary.is_active == True).first()
        dict_path = os.path.join(DICTIONARY_STORAGE_PATH, active_dict.filename) if active_dict else None
        dict_id = active_dict.id if active_dict else None
        db_sync.close()
        
        cleaner = get_cleaner()
        result_df = await cleaner.process_async(df, progress_callback=progress_callback, dict_path=dict_path)
        
        # Apply column reordering logic
        try:
            sample_path = os.path.join(os.path.dirname(__file__), "../dataset/sample.csv")
            sample_df = pd.read_csv(sample_path, nrows=0)
            expected_cols = sample_df.columns.tolist()
        except Exception:
            expected_cols = ['Ngày', 'Mã HS', 'Công ty NK', 'Tên hàng', 'DVT', 'Lượng', 'Giá trị', 'Đơn giá', 'Hãng', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Công suất', 'Quốc gia', 'Châu lục', 'MDSD', 'Công ty XK', 'Incoterms', 'Method_of_Payment', 'Công suất.1', 'Loại 1', 'Loại 2', 'Năm']

        trang_thai = result_df['Trạng Thái'] if 'Trạng Thái' in result_df.columns else None
        do_tu_tin = result_df['Độ Tự Tin (%)'] if 'Độ Tự Tin (%)' in result_df.columns else None
        
        result_df = result_df.reindex(columns=expected_cols)
        
        if trang_thai is not None:
            result_df['Trạng thái'] = trang_thai
        if do_tu_tin is not None:
            result_df['Độ tự tin'] = do_tu_tin
        
        await progress_callback("Generating Preview...")
        job["preview"] = []
        
        out_path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job_id}_{original_filename}")
        
        def save_file():
            if out_path.endswith('.csv'):
                result_df.to_csv(out_path, index=False, encoding='utf-8-sig')
            else:
                result_df.to_excel(out_path, index=False)
                
        await asyncio.to_thread(save_file)
            
        job["file_path"] = out_path
        job["status"] = "done"
        
        total_rows = len(result_df)
        total_columns = len(result_df.columns)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        db = database.SessionLocal()
        db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
        if db_job:
            db_job.status = "done"
            db_job.total_rows = total_rows
            db_job.total_columns = total_columns
            db_job.processing_time_ms = processing_time_ms
            db_job.dictionary_id = dict_id
            
            if dict_id:
                usage = models.DictionaryUsage(dictionary_id=dict_id, job_id=job_id)
                db.add(usage)
                
            db.commit()
            
            # trigger post-upload hook to cleanup old files
            cleanup_old_files(db_job.user_id, db)
            
        db.close()
        
        await job["event_queue"].put({"event": "done", "data": "Processing complete"})
        
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        
        db = database.SessionLocal()
        db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
        if db_job:
            db_job.status = "error"
            db_job.error_message = str(e)
            db.commit()
        db.close()
        
        await job["event_queue"].put({"event": "error", "data": str(e)})
    finally:
        remove_file(temp_path)

@app.get("/stream/{job_id}")
async def stream(job_id: str, current_user: models.User = Depends(get_user_from_token_query), db: Session = Depends(database.get_db)):
    import json
    
    db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if db_job and db_job.user_id != current_user.id:
        return EventSourceResponse(iter([{"data": json.dumps({"event": "error", "data": "Access Denied"})}] ))

    async def event_generator():
        job = jobs.get(job_id)
        if not job:
            yield {"data": json.dumps({"event": "error", "data": "Job not found"})}
            return
            
        while True:
            event = await job["event_queue"].get()
            yield {"data": json.dumps(event)}
            if event["event"] in ("done", "error"):
                break
    return EventSourceResponse(event_generator())

@app.get("/api/jobs/{job_id}/preview")
def get_job_preview(job_id: str, skip: int = 0, limit: int = 100, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if not db_job or db_job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
    if db_job.status != "done":
        raise HTTPException(status_code=400, detail="Job not done yet")
    
    out_path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job_id}_{db_job.filename}")
    if not os.path.exists(out_path):
        raise HTTPException(status_code=404, detail="Data file not found")
        
    try:
        if out_path.endswith('.csv'):
            df = pd.read_csv(out_path, skiprows=range(1, skip + 1), nrows=limit)
        else:
            df = pd.read_excel(out_path, skiprows=range(1, skip + 1), nrows=limit)
        return {"preview": df.fillna("").to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}/download")
def download_result(job_id: str, current_user: models.User = Depends(get_user_from_token_query), db: Session = Depends(database.get_db)):
    db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if not db_job or db_job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    out_path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job_id}_{db_job.filename}")
    if not os.path.exists(out_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        out_path, 
        media_type="application/octet-stream", 
        filename=f"cleaned_{db_job.filename}"
    )

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if not db_job or db_job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    out_path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job_id}_{db_job.filename}")
    remove_file(out_path)
    db.delete(db_job)
    db.commit()
    if job_id in jobs:
        del jobs[job_id]
        
    return {"message": "Deleted successfully"}

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/api/auth/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/jobs")
def get_user_jobs(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    user_jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.user_id == current_user.id).order_by(models.ProcessingJob.created_at.desc()).all()
    return {"jobs": [{"id": j.id, "filename": j.filename, "status": j.status, "created_at": j.created_at, "total_rows": j.total_rows, "total_columns": j.total_columns, "processing_time_ms": j.processing_time_ms} for j in user_jobs]}

@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    j = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id, models.ProcessingJob.user_id == current_user.id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": j.id, "filename": j.filename, "status": j.status, "created_at": j.created_at, "total_rows": j.total_rows, "total_columns": j.total_columns, "processing_time_ms": j.processing_time_ms, "error_message": j.error_message}

@app.get("/api/admin/system_status")
def admin_status(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")
    users_count = db.query(models.User).count()
    jobs_count = db.query(models.ProcessingJob).count()
    return {"users_count": users_count, "jobs_count": jobs_count}

# =======================================================
# Dictionary Management Endpoints
# =======================================================

@app.post("/api/dictionaries/upload")
async def upload_dictionary(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    out_path = os.path.join(DICTIONARY_STORAGE_PATH, filename)
    
    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    count = db.query(models.Dictionary).count()
    is_active = (count == 0)
    
    new_dict = models.Dictionary(
        filename=filename,
        user_id=current_user.id,
        is_active=is_active
    )
    db.add(new_dict)
    db.commit()
    db.refresh(new_dict)
    
    return {"id": new_dict.id, "filename": file.filename, "is_active": new_dict.is_active, "message": "Uploaded successfully."}

@app.get("/api/dictionaries")
def list_dictionaries(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    dicts = db.query(models.Dictionary).order_by(models.Dictionary.created_at.desc()).all()
    return {"dictionaries": [
        {
            "id": d.id, 
            "filename": d.filename.split('_', 1)[1] if '_' in d.filename else d.filename, 
            "is_active": d.is_active, 
            "created_at": d.created_at,
            "user_id": d.user_id
        } 
        for d in dicts
    ]}

@app.post("/api/dictionaries/{dict_id}/activate")
def activate_dictionary(dict_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    d = db.query(models.Dictionary).filter(models.Dictionary.id == dict_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dictionary not found.")
        
    db.query(models.Dictionary).update({"is_active": False})
    
    d.is_active = True
    db.commit()
    
    return {"message": "Dictionary activated successfully."}

@app.get("/api/dictionaries/{dict_id}/download")
def download_dictionary(dict_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    d = db.query(models.Dictionary).filter(models.Dictionary.id == dict_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dictionary not found.")
        
    file_path = os.path.join(DICTIONARY_STORAGE_PATH, d.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dictionary file not found on disk.")
        
    return FileResponse(
        file_path, 
        media_type="text/csv", 
        filename=d.filename.split('_', 1)[1] if '_' in d.filename else d.filename
    )

@app.delete("/api/dictionaries/{dict_id}")
def delete_dictionary(dict_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    d = db.query(models.Dictionary).filter(models.Dictionary.id == dict_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dictionary not found.")
    
    path = os.path.join(DICTIONARY_STORAGE_PATH, d.filename)
    if os.path.exists(path):
        os.remove(path)
        
    db.delete(d)
    db.commit()
    
    return {"message": "Deleted successfully."}

@app.get("/api/dictionaries/stats")
def dictionary_stats(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    from sqlalchemy import func
    stats = db.query(
        models.DictionaryUsage.dictionary_id, 
        func.count(models.DictionaryUsage.id).label('usage_count')
    ).group_by(models.DictionaryUsage.dictionary_id).all()
    
    return {"stats": [{"dictionary_id": s.dictionary_id, "usage_count": s.usage_count} for s in stats]}

# =======================================================
# Automated Dictionary Generation (Wizard)
# =======================================================

def load_robust_df(content, filename):
    """Robustly load CSV or Excel, handling headers and encodings."""
    is_csv = filename.endswith('.csv')
    if is_csv:
        for enc in ['utf-8', 'latin1', 'utf-8-sig']:
            try:
                # Try skipping 9 rows (common in this project's data)
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str, skiprows=9)
                if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns:
                    return df
                # Fallback to no skip
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str)
                if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns:
                    return df
            except Exception:
                continue
        # Last resort
        return pd.read_csv(io.BytesIO(content), encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype=str)
    else:
        try:
            df = pd.read_excel(io.BytesIO(content), dtype=str, skiprows=9)
            if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns:
                return df
            return pd.read_excel(io.BytesIO(content), dtype=str)
        except Exception:
            return pd.read_excel(io.BytesIO(content), dtype=str)

@app.post("/api/dictionaries/generate/step1")
async def generate_draft(
    file: UploadFile = File(...),
    use_llm: bool = Query(True),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Step 1: Raw Upload -> Draft Excel with 3 sheets"""
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload .xlsx or .csv")
        
    try:
        content = await file.read()
        raw_df = load_robust_df(content, file.filename)
            
        generator = DictionaryGenerator(groq_api_key=os.environ.get("GROQ_API_KEY"))
        
        # Run clustering in a separate thread
        draft_df, processed_raw_df = await asyncio.to_thread(
            generator.generate_draft_taxonomy, 
            raw_df, 
            use_llm=use_llm
        )
        
        # Convert draft_df to Excel in memory with 3 sheets (to match original repo)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Phân loại (để review)
            df_export = draft_df[['Keyword', 'Mã HS', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Cluster_ID']].copy()
            df_export.to_excel(writer, sheet_name='Phân loại', index=False)
            
            # Sheet 2: Chi tiết (để tham khảo)
            draft_df.to_excel(writer, sheet_name='Chi tiết Cluster', index=False)
            
            # Sheet 3: Dữ liệu raw đã gán cluster
            df_raw_export = processed_raw_df[['HS_Code', 'Detailed_Product', '_clean', '_cluster']].copy()
            df_raw_export.columns = ['Mã HS', 'Tên hàng gốc', 'Đã làm sạch', 'Cluster_ID']
            df_raw_export.to_excel(writer, sheet_name='Raw + Cluster', index=False)
            
        output.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="draft_taxonomy_{uuid.uuid4().hex[:8]}.xlsx"'
        }
        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")

@app.post("/api/dictionaries/generate/step2")
async def finalize_dictionary(
    raw_file: UploadFile = File(...),
    draft_file: UploadFile = File(...),
    dictionary_name: str = Query(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Step 2: Draft + Raw Upload -> Final Dictionary CSV"""
    if not dictionary_name.endswith('.csv'):
        dictionary_name += '.csv'
        
    print(f"DEBUG: Finalizing dictionary {dictionary_name} for user {current_user.username}")
    try:
        # Read raw file using robust loader
        raw_content = await raw_file.read()
        raw_df = load_robust_df(raw_content, raw_file.filename)
        print(f"DEBUG: Raw file loaded: {len(raw_df)} rows")
            
        # Read reviewed draft file
        draft_content = await draft_file.read()
        # Sheet 1: Taxonomy to be finalized
        draft_df = pd.read_excel(io.BytesIO(draft_content), sheet_name=0, dtype=str)
        print(f"DEBUG: Draft taxonomy loaded: {len(draft_df)} groups")
        
        # Try to read Sheet 3 (Raw + Cluster) from the SAME draft file
        # This is where the Cluster_ID mapping is stored
        try:
            raw_with_cluster_df = pd.read_excel(io.BytesIO(draft_content), sheet_name='Raw + Cluster', dtype=str)
            print(f"DEBUG: Cluster mapping found in draft file: {len(raw_with_cluster_df)} rows")
        except Exception as e:
            print(f"WARNING: Could not find 'Raw + Cluster' sheet in draft: {e}. Falling back to regex matching.")
            raw_with_cluster_df = None
        
        generator = DictionaryGenerator(groq_api_key=os.environ.get("GROQ_API_KEY"))
        
        # Extract keywords
        # We pass raw_with_cluster_df instead of original raw_df if we found the mapping
        final_dict_df = await asyncio.to_thread(
            generator.extract_keywords_for_taxonomy, 
            draft_df, 
            raw_with_cluster_df if raw_with_cluster_df is not None else raw_df
        )
        
        # Save to storage
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{dictionary_name}"
        out_path = os.path.join(DICTIONARY_STORAGE_PATH, filename)
        
        final_dict_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"DEBUG: Dictionary saved to {out_path}")
        
        # Register in database
        new_dict = models.Dictionary(
            filename=filename,
            user_id=current_user.id,
            is_active=False
        )
        db.add(new_dict)
        db.commit()
        db.refresh(new_dict)
        
        return {
            "id": new_dict.id, 
            "filename": dictionary_name, 
            "message": "Dictionary generated and saved successfully."
        }
    except Exception as e:
        print(f"ERROR in Step 2: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error finalizing dictionary: {str(e)}")


