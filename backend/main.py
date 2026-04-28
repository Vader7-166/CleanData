from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Query
from fastapi.responses import FileResponse
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

from .core.data_cleaner import get_cleaner
from . import models, auth, database
from .database import engine

PROCESSED_STORAGE_PATH = "backend/storage/processed"
os.makedirs(PROCESSED_STORAGE_PATH, exist_ok=True)

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
            
        cleaner = get_cleaner()
        # process_async currently blocks, we should run it as a task but it's an async function.
        # we can just await it since we'll add asyncio.sleep(0) inside it.
        result_df = await cleaner.process_async(df, progress_callback=progress_callback)
        
        # Apply column reordering logic
        try:
            import os
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
        # We no longer keep total preview in memory, it will be lazy loaded.
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


