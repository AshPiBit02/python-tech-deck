import uuid
from pathlib import Path
from fastapi import FastAPI,File,HTTPException,UploadFile

app=FastAPI(title="Save File to Disk")

UPLOAD_DIR=Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_SIZE=5*1024*1024 

@app.post("/upload/save")
async def save(file:UploadFile=File(...)):
    dest=UPLOAD_DIR/f"{uuid.uuid4().hex}{Path(file.filename or '').suffix}"
    size=0
    with dest.open("wb") as out:
        while chunk:=await file.read(1024*1024):
            size+=len(chunk)
            if size >MAX_SIZE:
                out.close()
                dest.unlink()
                raise HTTPException(status_code=413,detail="File too large (max 5 MB)")
            out.write(chunk)
    return {"saved_as":dest.name,"size":size}