from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
import shutil
import pandas as pd
import os
from datetime import datetime

from .core.data_cleaner import get_cleaner
from .database import engine, Base
# from .models import ... (all models removed)

app = FastAPI(title="Data Cleaning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    print("Loading model...")
    # Preload the model on startup
    get_cleaner()
    print("Model loaded.")

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx')):
         raise HTTPException(status_code=400, detail="Invalid file format.")
    
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    cleaner = get_cleaner()
    result_df = cleaner.process(df)
    
    out_path = f"cleaned_{file.filename}"
    if out_path.endswith('.csv'):
        result_df.to_csv(out_path, index=False)
    else:
        result_df.to_excel(out_path, index=False)
        
    # Task to remove both input and output files after response is sent
    async def cleanup():
        remove_file(file_path)
        remove_file(out_path)

    return FileResponse(
        out_path, 
        media_type="application/octet-stream", 
        filename=out_path,
        background=BackgroundTask(cleanup)
    )
