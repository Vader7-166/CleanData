from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status, Query, BackgroundTasks
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
import re
import uuid
import asyncio
import time
import io
import traceback
from typing import List
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

ACTIVE_GEN_JOBS = {}
TEMP_DRAFT_STORAGE_PATH = "backend/storage/temp_drafts"
os.makedirs(TEMP_DRAFT_STORAGE_PATH, exist_ok=True)

from sqlalchemy import text
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE dictionaries ADD COLUMN is_active BOOLEAN DEFAULT FALSE"))
except Exception as e:
    pass

# Migration: add hs_code_prefixes to dictionaries
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE dictionaries ADD COLUMN hs_code_prefixes TEXT"))
except Exception:
    pass

# Migration: add batch_id and transaction_type to processing_jobs
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE processing_jobs ADD COLUMN batch_id TEXT"))
except Exception:
    pass
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE processing_jobs ADD COLUMN transaction_type TEXT"))
except Exception:
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

# Global in-memory cache for HS Codes
hs_customs_cache = {}

@app.on_event("startup")
def startup_event():
    global hs_customs_cache
    print("Loading model on startup...")
    get_cleaner()
    print("Model loaded.")
    
    print("Loading offline HS Customs Reference into memory...")
    try:
        db = database.SessionLocal()
        records = db.query(models.HSCustomsReference).all()
        for r in records:
            hs_customs_cache[r.hs_code] = {
                "level": r.level,
                "description_vn": r.description_vn
            }
        print(f"Loaded {len(hs_customs_cache)} HS code references into cache.")
    except Exception as e:
        print(f"Error loading HS customs cache: {e}")
    finally:
        db.close()

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
            
            # Delete dictionary usage records referencing this job
            db.query(models.DictionaryUsage).filter(models.DictionaryUsage.job_id == j.id).delete()
            
            db.delete(j)
            if j.id in jobs:
                del jobs[j.id]
        db.commit()

def load_dataframe_sync(path, csv_mode):
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

import json

async def process_batch(batch_id: str, tasks: list):
    for task in tasks:
        job = jobs.get(task['job_id'])
        if job and job.get("status") == "cancelled":
            remove_file(task['temp_path'])
            continue
            
        if job:
            job["status"] = "processing"
            db_sync = database.SessionLocal()
            db_job = db_sync.query(models.ProcessingJob).filter(models.ProcessingJob.id == task['job_id']).first()
            if db_job and db_job.status != 'cancelled':
                db_job.status = "processing"
                db_sync.commit()
            db_sync.close()
        await process_job(task['job_id'], task['temp_path'], task['filename'])
    
    # Mark batch as done
    db_sync = database.SessionLocal()
    db_batch = db_sync.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if db_batch and db_batch.status != 'cancelled':
        db_batch.status = "done"
        db_sync.commit()
    db_sync.close()

@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...), 
    transaction_types: str = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    active_dict = db.query(models.Dictionary).filter(models.Dictionary.is_active == True).first()
    if not active_dict:
        raise HTTPException(
            status_code=400, 
            detail="Không có bộ từ điển nào được kích hoạt. Vui lòng upload và chọn một bộ từ điển trước khi Clean Data."
        )

    types_map = {}
    if transaction_types:
        try:
            types_map = json.loads(transaction_types)
        except Exception:
            pass

    batch_id = str(uuid.uuid4())
    job_id = batch_id # We now have 1:1 relation for batch:job
    new_batch = models.Batch(id=batch_id, user_id=current_user.id, status="processing")
    db.add(new_batch)
    
    merged_temp_path = f"temp_{job_id}_merged.csv"
    first_file = True
    processed_any = False
    
    for file in files:
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            continue
            
        t_type = types_map.get(file.filename)
        chunk_temp_path = f"temp_chunk_{uuid.uuid4()}_{file.filename}"
        
        with open(chunk_temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        df_chunk = load_dataframe_sync(chunk_temp_path, file.filename.endswith('.csv'))
        if df_chunk is not None and not df_chunk.empty:
            df_chunk['Tên file nguồn'] = file.filename
            if t_type:
                df_chunk['transaction_type_override'] = t_type
            
            df_chunk.to_csv(merged_temp_path, mode='a', header=first_file, index=False, encoding='utf-8-sig')
            first_file = False
            processed_any = True
            
        remove_file(chunk_temp_path)

    if not processed_any:
        db.rollback()
        raise HTTPException(status_code=400, detail="No valid data found in CSV or Excel files.")

    new_job = models.ProcessingJob(
        id=job_id, 
        filename="merged_upload.csv", 
        status="pending", 
        user_id=current_user.id,
        batch_id=batch_id,
        transaction_type=None
    )
    db.add(new_job)
    db.commit()

    jobs[job_id] = {
        "status": "pending",
        "file_path": None,
        "preview": None,
        "error": None,
        "transaction_type": None,
        "event_queue": asyncio.Queue()
    }
    
    tasks_to_run = [{
        "job_id": job_id,
        "temp_path": merged_temp_path,
        "filename": "merged_upload.csv"
    }]
    asyncio.create_task(process_batch(batch_id, tasks_to_run))
    return {"batch_id": batch_id, "job_ids": [job_id], "message": f"Upload successful, {len(files)} files merged."}

async def process_job(job_id: str, temp_path: str, original_filename: str):
    job = jobs.get(job_id)
    if not job:
        return
        
    async def progress_callback(msg):
        job["progress_msg"] = msg
        await job["event_queue"].put({"event": "progress", "data": msg})

    try:
        start_time = time.time()
        await progress_callback("Loading Data...")
        if job.get("status") == "cancelled":
            return
            
        is_csv = original_filename.endswith('.csv')
        
        # We don't need to define load_dataframe inside process_job anymore
        df = await asyncio.to_thread(load_dataframe_sync, temp_path, is_csv)
            
        db_sync = database.SessionLocal()
        
        # Fetch all active dictionaries and sort them: User first, Admin last (Admin overwrites User)
        active_dicts = db_sync.query(models.Dictionary).join(models.User).filter(models.Dictionary.is_active == True).all()
        active_dicts.sort(key=lambda d: 1 if d.owner.role == 'admin' else 0)
        
        dict_paths = [os.path.join(DICTIONARY_STORAGE_PATH, d.filename) for d in active_dicts]
        dict_ids = [d.id for d in active_dicts]
        db_sync.close()
        
        cleaner = get_cleaner()
        result_df = await cleaner.process_async(df, progress_callback=progress_callback, dict_paths=dict_paths, transaction_type=job.get("transaction_type"))
        
        # Apply column reordering logic
        try:
            sample_path = os.path.join(os.path.dirname(__file__), "../dataset/sample.csv")
            sample_df = pd.read_csv(sample_path, nrows=0)
            expected_cols = sample_df.columns.tolist()
        except Exception:
            expected_cols = ['Ngày', 'Tháng', 'Mã HS', 'Công ty NK', 'Tên hàng', 'DVT', 'Lượng', 'Giá trị', 'Đơn giá', 'Hãng', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Công suất', 'Quốc gia', 'Châu lục', 'MDSD', 'Công ty XK', 'Incoterms', 'Phương thức thanh toán', 'Loại 1', 'Loại 2', 'Năm', 'Loại giao dịch']

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
            db_job.dictionary_id = dict_ids[-1] if dict_ids else None
            
            for d_id in dict_ids:
                usage = models.DictionaryUsage(dictionary_id=d_id, job_id=job_id)
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


@app.get("/api/batches/{batch_id}")
def get_batch_status(batch_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch or batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    db_jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.batch_id == batch_id).all()
    job_statuses = []
    for j in db_jobs:
        live_job = jobs.get(j.id)
        current_status = live_job["status"] if live_job else j.status
        job_statuses.append({
            "id": j.id,
            "filename": j.filename,
            "status": current_status,
            "progress_msg": live_job.get("progress_msg", "") if live_job else "",
            "transaction_type": j.transaction_type,
            "error_message": j.error_message
        })
        
    return {
        "id": batch.id,
        "status": batch.status,
        "created_at": batch.created_at,
        "jobs": job_statuses
    }

@app.delete("/api/batches/{batch_id}")
def delete_batch(batch_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch or batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    batch.status = 'cancelled'
    db_jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.batch_id == batch_id).all()
    for j in db_jobs:
        if j.status in ['pending', 'processing']:
            j.status = 'cancelled'
            if j.id in jobs:
                jobs[j.id]["status"] = "cancelled"
                jobs[j.id]["progress_msg"] = "Cancelled by user"
                # Remove temporary files if any
                temp_path = f"temp_chunk_*"
                # we don't know the exact temp chunk, but we can try to clean merged_temp_path 
                merged_temp_path = f"temp_{j.id}_merged.csv"
                remove_file(merged_temp_path)
    
    db.commit()
    return {"message": "Batch cancelled"}

import zipfile
import io
from fastapi.responses import StreamingResponse

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

@app.get("/api/batches/{batch_id}/download-merged")
def download_batch_merged(batch_id: str, current_user: models.User = Depends(get_user_from_token_query), db: Session = Depends(database.get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch or batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.batch_id == batch_id, models.ProcessingJob.status == "done").all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No completed jobs found for this batch")
        
    all_dfs = []
    for job in jobs:
        path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job.id}_{job.filename}")
        if os.path.exists(path):
            try:
                df = pd.read_excel(path) if path.endswith(('.xlsx', '.xls')) else pd.read_csv(path)
                df['Tên file nguồn'] = job.filename
                all_dfs.append(df)
            except Exception:
                pass
            
    if not all_dfs:
        raise HTTPException(status_code=404, detail="Files not found on disk")
        
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        merged_df.to_excel(writer, index=False)
    output.seek(0)
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=batch_merged_{batch_id}.xlsx"}
    )

@app.get("/api/batches/{batch_id}/download-zip")
def download_batch_zip(batch_id: str, current_user: models.User = Depends(get_user_from_token_query), db: Session = Depends(database.get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch or batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.batch_id == batch_id, models.ProcessingJob.status == "done").all()
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for job in jobs:
            path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job.id}_{job.filename}")
            if os.path.exists(path):
                zip_file.write(path, arcname=f"cleaned_{job.filename}")
                
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.zip"}
    )

@app.get("/api/batches/{batch_id}/insights")
def batch_insights(batch_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch or batch.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    jobs = db.query(models.ProcessingJob).filter(models.ProcessingJob.batch_id == batch_id, models.ProcessingJob.status == "done").all()
    
    if not jobs:
        return {"product_lines": [], "nc_lk_ratio": [], "top_companies": []}
        
    all_dfs = []
    for job in jobs:
        path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job.id}_{job.filename}")
        if os.path.exists(path):
            try:
                # pandas usecols requires columns to exist. If a column is missing, it will throw an error.
                # So we read all and then filter.
                df = pd.read_excel(path) if path.endswith(('.xlsx', '.xls')) else pd.read_csv(path)
                keep_cols = [c for c in ['Dòng SP', 'Loại', 'Công ty NK', 'Công ty XK', 'Giá trị', 'Loại giao dịch', 'Trạng Thái', 'Lớp 1'] if c in df.columns]
                df = df[keep_cols]
                all_dfs.append(df)
            except Exception:
                pass
            
    if not all_dfs:
         return {"product_lines": [], "nc_lk_ratio": [], "top_companies": [], "top_hs_codes": [], "total_rows": 0, "needs_review_count": 0}
         
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    total_rows = len(merged_df)
    needs_review_count = len(merged_df[merged_df['Trạng Thái'] == 'Cần kiểm tra']) if 'Trạng Thái' in merged_df.columns else 0
    
    pl_counts = merged_df['Dòng SP'].value_counts().reset_index() if 'Dòng SP' in merged_df.columns else pd.DataFrame(columns=['name', 'value'])
    if not pl_counts.empty: pl_counts.columns = ['name', 'value']
    
    hs_counts = merged_df['Lớp 1'].value_counts().reset_index() if 'Lớp 1' in merged_df.columns else pd.DataFrame(columns=['name', 'value'])
    if not hs_counts.empty: hs_counts.columns = ['name', 'value']
    top_hs = hs_counts.head(5).to_dict('records') if not hs_counts.empty else []
    
    nc_lk_counts = merged_df['Loại'].value_counts().reset_index() if 'Loại' in merged_df.columns else pd.DataFrame(columns=['name', 'value'])
    if not nc_lk_counts.empty: nc_lk_counts.columns = ['name', 'value']
    
    company_vals = []
    for _, row in merged_df.iterrows():
        comp = row.get('Công ty NK') if row.get('Loại giao dịch') == 'Nhập khẩu' else row.get('Công ty XK')
        if pd.notna(comp) and comp:
            val = pd.to_numeric(row.get('Giá trị'), errors='coerce')
            if pd.notna(val):
                company_vals.append({'name': comp, 'value': val})
                
    comp_df = pd.DataFrame(company_vals)
    top_comps = []
    if not comp_df.empty:
        top_comps = comp_df.groupby('name')['value'].sum().sort_values(ascending=False).head(5).reset_index().to_dict('records')
        
    return {
        "product_lines": pl_counts.to_dict('records') if not pl_counts.empty else [],
        "nc_lk_ratio": nc_lk_counts.to_dict('records') if not nc_lk_counts.empty else [],
        "top_companies": top_comps,
        "top_hs_codes": top_hs,
        "total_rows": total_rows,
        "needs_review_count": needs_review_count
    }

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if not db_job or db_job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access Denied")
        
    out_path = os.path.join(PROCESSED_STORAGE_PATH, f"cleaned_{job_id}_{db_job.filename}")
    remove_file(out_path)
    
    # Delete dictionary usage records referencing this job
    db.query(models.DictionaryUsage).filter(models.DictionaryUsage.job_id == job_id).delete()
    
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
    
    # Auto-extract HS code prefixes from the dictionary CSV
    hs_prefixes_str = None
    try:
        df_dict = pd.read_csv(out_path, encoding='utf-8-sig', usecols=['Mã HS'])
        hs_codes = df_dict['Mã HS'].dropna().astype(str)
        prefixes = set()
        for code in hs_codes:
            clean = ''.join(c for c in code if c.isdigit())
            if len(clean) >= 4:
                prefixes.add(clean[:4])
        if prefixes:
            hs_prefixes_str = ','.join(sorted(prefixes))
    except Exception:
        pass  # Column may not exist in all dictionaries
    
    new_dict = models.Dictionary(
        filename=filename,
        user_id=current_user.id,
        is_active=is_active,
        hs_code_prefixes=hs_prefixes_str
    )
    db.add(new_dict)
    db.commit()
    db.refresh(new_dict)
    
    return {"id": new_dict.id, "filename": file.filename, "is_active": new_dict.is_active, "hs_code_prefixes": new_dict.hs_code_prefixes, "message": "Uploaded successfully."}

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
def activate_dictionary(dict_id: int, active: bool = True, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    d = db.query(models.Dictionary).filter(models.Dictionary.id == dict_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dictionary not found.")
        
    d.is_active = active
    db.commit()
    
    return {"message": f"Dictionary {'activated' if active else 'deactivated'} successfully."}

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
        
    db.query(models.DictionaryUsage).filter(models.DictionaryUsage.dictionary_id == dict_id).delete()
    db.query(models.ProcessingJob).filter(models.ProcessingJob.dictionary_id == dict_id).update({"dictionary_id": None})
        
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
# HS Taxonomy Management Endpoints
# =======================================================

class HSTaxonomyCreate(BaseModel):
    hs_code_prefix: str
    dong_sp: str
    industry_name: str
    default_type: str  # "NC" or "LK"

class HSTaxonomyUpdate(BaseModel):
    dong_sp: str | None = None
    industry_name: str | None = None
    default_type: str | None = None

class HSTaxonomyBulkItem(BaseModel):
    hs_code_prefix: str
    dong_sp: str
    industry_name: str
    default_type: str

class HSTaxonomyBulkSave(BaseModel):
    items: list[HSTaxonomyBulkItem]

class HSCodeCheckRequest(BaseModel):
    hs_codes: list[str]

@app.get("/api/taxonomy")
def list_taxonomy(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    records = db.query(models.HSTaxonomy).order_by(models.HSTaxonomy.hs_code_prefix).all()
    return {"taxonomy": [
        {
            "id": r.id,
            "hs_code_prefix": r.hs_code_prefix,
            "dong_sp": r.dong_sp,
            "industry_name": r.industry_name,
            "default_type": r.default_type,
            "source": r.source,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in records
    ]}

@app.post("/api/taxonomy")
def create_taxonomy(
    data: HSTaxonomyCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    import re as _re
    clean_code = _re.sub(r'\D', '', data.hs_code_prefix)
    if not clean_code:
        raise HTTPException(status_code=400, detail="Invalid HS code prefix.")
    if data.default_type not in ('NC', 'LK'):
        raise HTTPException(status_code=400, detail="default_type must be 'NC' or 'LK'.")
    
    existing = db.query(models.HSTaxonomy).filter(models.HSTaxonomy.hs_code_prefix == clean_code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"HS code prefix '{clean_code}' already exists.")
    
    record = models.HSTaxonomy(
        hs_code_prefix=clean_code,
        dong_sp=data.dong_sp,
        industry_name=data.industry_name,
        default_type=data.default_type,
        source='user_input'
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "message": "Created successfully."}

@app.put("/api/taxonomy/{taxonomy_id}")
def update_taxonomy(
    taxonomy_id: int,
    data: HSTaxonomyUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    record = db.query(models.HSTaxonomy).filter(models.HSTaxonomy.id == taxonomy_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Taxonomy record not found.")
    
    if data.dong_sp is not None:
        record.dong_sp = data.dong_sp
    if data.industry_name is not None:
        record.industry_name = data.industry_name
    if data.default_type is not None:
        if data.default_type not in ('NC', 'LK'):
            raise HTTPException(status_code=400, detail="default_type must be 'NC' or 'LK'.")
        record.default_type = data.default_type
    
    db.commit()
    return {"message": "Updated successfully."}

@app.delete("/api/taxonomy/{taxonomy_id}")
def delete_taxonomy(
    taxonomy_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    record = db.query(models.HSTaxonomy).filter(models.HSTaxonomy.id == taxonomy_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Taxonomy record not found.")
    
    db.delete(record)
    db.commit()
    return {"message": "Deleted successfully."}

@app.post("/api/taxonomy/check-hs-codes")
async def check_hs_codes(
    data: HSCodeCheckRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Accept a list of raw HS codes, query the DB (longest-prefix matching),
    trigger the crawler for missing ones, and return resolved + unresolved lists.
    """
    import re as _re
    from .core.crawler import crawl_hs_code

    resolved = []
    unresolved = []

    for raw_code in data.hs_codes:
        clean_code = _re.sub(r'\D', '', str(raw_code))
        if not clean_code or len(clean_code) < 4:
            continue

        # Try longest-prefix matching in DB
        match = None
        for length in [len(clean_code), 10, 8, 6, 4]:
            if length > len(clean_code):
                continue
            prefix = clean_code[:length]
            match = db.query(models.HSTaxonomy).filter(
                models.HSTaxonomy.hs_code_prefix == prefix
            ).first()
            if match:
                break

        if match:
            resolved.append({
                "hs_code": clean_code,
                "dong_sp": match.dong_sp,
                "industry_name": match.industry_name,
                "default_type": match.default_type,
                "source": match.source,
            })
            continue

        # Try in-memory offline dictionary
        from backend.main import hs_customs_cache
        if clean_code in hs_customs_cache:
            cache_match = hs_customs_cache[clean_code]
            # Infer dong_sp and default_type from the crawler logic
            from .core.crawler import infer_dong_sp, infer_default_type
            resolved.append({
                "hs_code": clean_code,
                "dong_sp": infer_dong_sp(clean_code),
                "industry_name": cache_match['description_vn'],
                "default_type": infer_default_type(cache_match['description_vn']),
                "source": "offline_cache",
            })
            continue

        # Try online crawler
        try:
            crawl_result = await crawl_hs_code(clean_code)
            if crawl_result:
                # Save to DB
                new_record = models.HSTaxonomy(
                    hs_code_prefix=crawl_result['hs_code_prefix'],
                    dong_sp=crawl_result['dong_sp'],
                    industry_name=crawl_result['industry_name'],
                    default_type=crawl_result['default_type'],
                    source='crawled'
                )
                db.add(new_record)
                db.commit()

                resolved.append({
                    "hs_code": clean_code,
                    "dong_sp": crawl_result['dong_sp'],
                    "industry_name": crawl_result['industry_name'],
                    "default_type": crawl_result['default_type'],
                    "source": "crawled",
                })
                continue
        except Exception as e:
            print(f"DEBUG: Crawler failed for {clean_code}: {e}")

        # Unresolved
        unresolved.append({"hs_code": clean_code})

    return {"resolved": resolved, "unresolved": unresolved}

@app.post("/api/taxonomy/bulk-save")
def bulk_save_taxonomy(
    data: HSTaxonomyBulkSave,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Save multiple taxonomy records from manual user input (wizard interception)."""
    import re as _re
    saved = 0
    for item in data.items:
        clean_code = _re.sub(r'\D', '', item.hs_code_prefix)
        if not clean_code:
            continue
        if item.default_type not in ('NC', 'LK'):
            continue

        existing = db.query(models.HSTaxonomy).filter(
            models.HSTaxonomy.hs_code_prefix == clean_code
        ).first()
        if existing:
            existing.dong_sp = item.dong_sp
            existing.industry_name = item.industry_name
            existing.default_type = item.default_type
            existing.source = 'user_input'
        else:
            record = models.HSTaxonomy(
                hs_code_prefix=clean_code,
                dong_sp=item.dong_sp,
                industry_name=item.industry_name,
                default_type=item.default_type,
                source='user_input'
            )
            db.add(record)
        saved += 1

    db.commit()
    return {"message": f"Saved {saved} taxonomy records.", "count": saved}

@app.post("/api/taxonomy/bulk-upload")
async def bulk_upload_taxonomy(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Bulk import taxonomy from CSV/Excel with columns: hs_code_prefix, dong_sp, industry_name, default_type."""
    import re as _re
    content = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(content), dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    required_cols = ['hs_code_prefix', 'dong_sp', 'industry_name', 'default_type']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

    saved = 0
    for _, row in df.iterrows():
        clean_code = _re.sub(r'\D', '', str(row['hs_code_prefix']))
        if not clean_code:
            continue
        d_type = str(row['default_type']).strip().upper()
        if d_type not in ('NC', 'LK'):
            continue

        existing = db.query(models.HSTaxonomy).filter(
            models.HSTaxonomy.hs_code_prefix == clean_code
        ).first()
        if existing:
            existing.dong_sp = str(row['dong_sp'])
            existing.industry_name = str(row['industry_name'])
            existing.default_type = d_type
            existing.source = 'user_input'
        else:
            record = models.HSTaxonomy(
                hs_code_prefix=clean_code,
                dong_sp=str(row['dong_sp']),
                industry_name=str(row['industry_name']),
                default_type=d_type,
                source='user_input'
            )
            db.add(record)
        saved += 1

    db.commit()
    return {"message": f"Imported {saved} taxonomy records.", "count": saved}

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
                if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns or 'Actual_Detail_Product' in df.columns or 'Actual_Detailed_Product' in df.columns:
                    return df
                # Fallback to no skip
                df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip', low_memory=False, dtype=str)
                if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns or 'Actual_Detail_Product' in df.columns or 'Actual_Detailed_Product' in df.columns:
                    return df
            except Exception:
                continue
        # Last resort
        return pd.read_csv(io.BytesIO(content), encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype=str)
    else:
        try:
            df = pd.read_excel(io.BytesIO(content), dtype=str, skiprows=9)
            if 'HS_Code' in df.columns or 'Detailed_Product' in df.columns or 'Actual_Detail_Product' in df.columns or 'Actual_Detailed_Product' in df.columns:
                return df
            return pd.read_excel(io.BytesIO(content), dtype=str)
        except Exception:
            return pd.read_excel(io.BytesIO(content), dtype=str)


def _load_db_taxonomy():
    """Load all HSTaxonomy records from DB as a list of dicts."""
    db = database.SessionLocal()
    try:
        records = db.query(models.HSTaxonomy).all()
        return [
            {
                'hs_code_prefix': r.hs_code_prefix,
                'dong_sp': r.dong_sp,
                'industry_name': r.industry_name,
                'default_type': r.default_type,
            }
            for r in records
        ] if records else None
    finally:
        db.close()

def run_generation_task(job_id: str, raw_df: pd.DataFrame, use_llm: bool, deepseek_api_key: str, db_taxonomy: list):
    try:
        ACTIVE_GEN_JOBS[job_id]["status"] = "processing"
        
        def progress_callback(current, total, message):
            if job_id in ACTIVE_GEN_JOBS:
                ACTIVE_GEN_JOBS[job_id]["progress"] = {"current": current, "total": total, "message": message}
            
        generator = DictionaryGenerator(
            deepseek_api_key=deepseek_api_key,
            db_taxonomy=db_taxonomy
        )
        
        draft_df, processed_raw_df = generator.generate_draft_taxonomy(
            raw_df, 
            use_llm=use_llm,
            progress_callback=progress_callback
        )
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export = draft_df[['Keyword', 'Mã HS', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Cluster_ID']].copy()
            df_export.to_excel(writer, sheet_name='Phân loại', index=False)
            draft_df.to_excel(writer, sheet_name='Chi tiết Cluster', index=False)
            df_raw_export = processed_raw_df[['HS_Code', 'Detailed_Product', '_clean', '_cluster']].copy()
            df_raw_export.columns = ['Mã HS', 'Tên hàng gốc', 'Đã làm sạch', 'Cluster_ID']
            df_raw_export.to_excel(writer, sheet_name='Raw + Cluster', index=False)
            
        temp_file_path = os.path.join(TEMP_DRAFT_STORAGE_PATH, f"{job_id}.xlsx")
        with open(temp_file_path, "wb") as f:
            f.write(output.getvalue())
            
        ACTIVE_GEN_JOBS[job_id]["status"] = "done"
        ACTIVE_GEN_JOBS[job_id]["result_file"] = temp_file_path
        ACTIVE_GEN_JOBS[job_id]["progress"]["message"] = "Completed"
    except Exception as e:
        traceback.print_exc()
        if job_id in ACTIVE_GEN_JOBS:
            ACTIVE_GEN_JOBS[job_id]["status"] = "error"
            ACTIVE_GEN_JOBS[job_id]["error_message"] = str(e)

@app.post("/api/dictionaries/generate/step1")
async def generate_draft(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    use_llm: bool = Query(True),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Step 1: Raw Upload -> Initiate Background Task"""
    all_dfs = []
    for file in files:
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            continue
        content = await file.read()
        df = load_robust_df(content, file.filename)
        all_dfs.append(df)
        
    if not all_dfs:
        raise HTTPException(status_code=400, detail="No valid .xlsx or .csv files uploaded")
        
    try:
        raw_df = pd.concat(all_dfs, ignore_index=True)
        job_id = uuid.uuid4().hex
        
        ACTIVE_GEN_JOBS[job_id] = {
            "status": "pending",
            "progress": {"current": 0, "total": 0, "message": "Initializing..."},
            "result_file": None,
            "error_message": None
        }
        
        background_tasks.add_task(
            run_generation_task,
            job_id=job_id,
            raw_df=raw_df,
            use_llm=use_llm,
            deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY"),
            db_taxonomy=_load_db_taxonomy()
        )
        
        return {"job_id": job_id, "message": "Generation started in background"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error initiating draft generation: {str(e)}")

@app.post("/api/dictionaries/generate/hq-direct")
async def generate_hq_direct(
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(auth.get_current_user)
):
    """1-Step Dictionary Generation from HQ Labeled files"""
    all_dfs = []
    for file in files:
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            continue
        content = await file.read()
        df = load_robust_df(content, file.filename)
        all_dfs.append(df)
        
    if not all_dfs:
        raise HTTPException(status_code=400, detail="No valid .xlsx or .csv files uploaded")
        
    try:
        raw_df = pd.concat(all_dfs, ignore_index=True)
        db_tax = _load_db_taxonomy()
        generator = DictionaryGenerator(db_taxonomy=db_tax)
        df_res = generator.generate_dictionary_from_hq(raw_df)
        
        # Replace NaNs for JSON serialization
        df_res = df_res.replace({np.nan: None})
        preview_data = df_res.to_dict(orient="records")
        
        return {"message": "Success", "data": preview_data}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating from HQ files: {str(e)}")

class HQDirectSaveRequest(BaseModel):
    dictionary_name: str
    data: list

@app.post("/api/dictionaries/generate/hq-direct/save")
def save_hq_direct_dictionary(
    request: HQDirectSaveRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    dictionary_name = request.dictionary_name
    if not dictionary_name.endswith('.csv'):
        dictionary_name += '.csv'
    
    df = pd.DataFrame(request.data)
    
    # Ensure correct column order
    cols_order = ['Keyword', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Mã HS', 'Số lượng SP']
    df = df[[c for c in cols_order if c in df.columns]]
    
    file_path = os.path.join(DICTIONARY_STORAGE_PATH, dictionary_name)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    # Auto-extract HS code prefixes from the dictionary CSV
    hs_prefixes_str = None
    if 'Mã HS' in df.columns:
        prefixes = set()
        for code in df['Mã HS'].dropna().astype(str):
            clean = re.sub(r'\D', '', code)
            if len(clean) >= 4:
                prefixes.add(clean[:4])
        if prefixes:
            hs_prefixes_str = ','.join(sorted(prefixes))
            
    count = db.query(models.Dictionary).count()
    is_active = (count == 0)
    
    db_dict = models.Dictionary(
        filename=dictionary_name,
        hs_code_prefixes=hs_prefixes_str,
        user_id=current_user.id,
        is_active=is_active
    )
    db.add(db_dict)
    db.commit()
    db.refresh(db_dict)
    
    return {"message": "Dictionary saved successfully", "id": db_dict.id}

@app.get("/api/dictionaries/generate/status/{job_id}")
def get_generation_status(job_id: str, current_user: models.User = Depends(auth.get_current_user)):
    job = ACTIVE_GEN_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return {"job_id": job_id, **job}

@app.get("/api/dictionaries/generate/download/{job_id}")
def download_generation_draft(job_id: str, current_user: models.User = Depends(auth.get_current_user)):
    job = ACTIVE_GEN_JOBS.get(job_id)
    if not job or job["status"] != "done" or not job["result_file"]:
        raise HTTPException(status_code=404, detail="Result not available")
    
    file_path = job["result_file"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    headers = {
        'Content-Disposition': f'attachment; filename="draft_taxonomy_{job_id[:8]}.xlsx"'
    }
    return FileResponse(file_path, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/dictionaries/generate/step2")
async def finalize_dictionary(
    raw_files: List[UploadFile] = File(...),
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
        # Read raw files using robust loader
        all_raw_dfs = []
        for file in raw_files:
            raw_content = await file.read()
            df = load_robust_df(raw_content, file.filename)
            all_raw_dfs.append(df)
        raw_df = pd.concat(all_raw_dfs, ignore_index=True)
        print(f"DEBUG: Raw files loaded: {len(raw_df)} rows")
            
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
        
        generator = DictionaryGenerator(
            deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY"),
            db_taxonomy=_load_db_taxonomy()
        )
        
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


