from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import shutil
import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .core.data_cleaner import get_cleaner
from .database import engine, get_db, Base
from .models import User, ProcessingHistory

app = FastAPI(title="Data Cleaning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

@app.on_event("startup")
def startup_event():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    
    # Initialize admin user if empty
    db = next(get_db())
    if not db.query(User).filter(User.username == "admin").first():
        hashed_password = pwd_context.hash("secret")
        db_user = User(username="admin", hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
    db.close()

    print("Loading model...")
    # Preload the model on startup
    get_cleaner()
    print("Model loaded.")

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    
    # Insert History
    history = ProcessingHistory(user_id=user.id, filename=file.filename, timestamp=datetime.utcnow())
    db.add(history)
    db.commit()
    
    out_path = f"cleaned_{file.filename}"
    if out_path.endswith('.csv'):
        result_df.to_csv(out_path, index=False)
    else:
        result_df.to_excel(out_path, index=False)
        
    return FileResponse(out_path, media_type="application/octet-stream", filename=out_path)
