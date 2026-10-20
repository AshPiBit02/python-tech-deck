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

def add_record(record:dict)->None:
    with LOCK:
        records=load_records()
        records.append(record)
        DB_FILE.write_text(json.dumps(records,indent=2))

@app.post("/apply",status_code=201)
async def apply(name:str=Form(...,min_length=2,max_length=100),resume:UploadFile=File(...)):
    if not (resume.filename or "").lower().endswith(".pdf") or resume.content_type!="application/pdf":
        raise HTTPException(415,"Only PDF resumes are allowed")

    data=await resume.read(MAX_SIZE+1)
    if len(data)>MAX_SIZE:
        raise HTTPException(413,"Resume too large (max 2 MB)")

    if not data.startswith(b"%PDF-"):
        raise HTTPException(415,"File content is not a valid PDF")

    stored_name=f"{uuid.uuid4().hex}.pdf"
    (RESUME_DIR/stored_name).write_bytes(data)

    record={
        "id":uuid.uuid4().hex,
        "name":name.strip(),
        "original_filename":resume.filename,
        "stored_filename":stored_name,
        "size":len(data),
        "applied_at":datetime.now(timezone.utc).isoformat(),
    }

    add_record(record)
    return {
        "message":"Application received",
        "id":record["id"]
    }