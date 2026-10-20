import json
import threading
import uuid
from datetime import datetime,timezone
from pathlib import Path
from fastapi import FastAPI,File,Form,HTTPException,UploadFile

app=FastAPI(title="Resume Collector")

RESUME_DIR=Path("resumes")
DB_FILE=Path("application.json")
MAX_SIZE=2*1024*1024
LOCK=threading.lock() # protects the JSON file from concurrent writes

RESUME_DIR.mkdir(exist_ok=True)

def load_records()->list:
    if not DB_FILE.exists():
        return []
    return json.loads(DB_FILE.read_text())
