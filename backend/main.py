from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
import shutil
import pandas as pd
import numpy as np
import os
import uuid
import asyncio

from .core.data_cleaner import get_cleaner

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

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx')):
         raise HTTPException(status_code=400, detail="Invalid file format.")
    
    job_id = str(uuid.uuid4())
    temp_path = f"temp_{job_id}_{file.filename}"
    
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
        def generate_preview():
            return result_df.head(100).fillna("").to_dict(orient="records")
            
        job["preview"] = await asyncio.to_thread(generate_preview)
        
        out_path = f"cleaned_{job_id}_{original_filename}"
        
        def save_file():
            if out_path.endswith('.csv'):
                result_df.to_csv(out_path, index=False, encoding='utf-8-sig')
            else:
                result_df.to_excel(out_path, index=False)
                
        await asyncio.to_thread(save_file)
            
        job["file_path"] = out_path
        job["status"] = "done"
        await job["event_queue"].put({"event": "done", "data": "Processing complete"})
        
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        await job["event_queue"].put({"event": "error", "data": str(e)})
    finally:
        remove_file(temp_path)

@app.get("/stream/{job_id}")
async def stream(job_id: str):
    import json
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

@app.get("/api/preview/{job_id}")
def get_preview(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        if job["status"] == "error":
            raise HTTPException(status_code=500, detail=job["error"])
        raise HTTPException(status_code=400, detail="Job not done yet")
    return {"preview": job["preview"]}

@app.get("/download/{job_id}")
def download_result(job_id: str):
    job = jobs.get(job_id)
    if not job or not job.get("file_path"):
        raise HTTPException(status_code=404, detail="File not found")
        
    out_path = job["file_path"]
    
    def cleanup():
        remove_file(out_path)
        del jobs[job_id]
        
    return FileResponse(
        out_path, 
        media_type="application/octet-stream", 
        filename=out_path.split(f"_{job_id}_")[-1] if f"_{job_id}_" in out_path else out_path,
        background=BackgroundTask(cleanup)
    )
