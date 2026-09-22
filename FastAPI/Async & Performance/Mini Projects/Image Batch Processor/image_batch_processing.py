import asyncio
import io
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path
from typing import List,Annotated
from fastapi import FastAPI,UploadFile,File,BackgroundTasks,HTTPException
from PIL import Image

app=FastAPI(title="Image Batch Processor")

UPLOAD_DIR=Path("uploads")
THUMBNAIL_DIR=Path("thumbnails")
UPLOAD_DIR.mkdir(exist_ok=True)
THUMBNAIL_DIR.mkdir(exist_ok=True)

JOBS:dict[str,dict]={}

THUMBNAIL_SIZE=(200,200)

def resize_image_cpu_bound(source_path:Path,dest_path:Path)->dict:
    start=time.perf_counter()
    with Image.open(source_path) as img:
        img.thumbnail(THUMBNAIL_SIZE)
        img.save(dest_path)
    elapsed=time.perf_counter()-start
    return {"duration_seconds":round(elapsed,3),"thumbnail_path":str(dest_path)}

async def process_single_image(job_id:str,filename:str,source_path:Path):
    dest_path=THUMBNAIL_DIR/f"thumb_{filename}"
    loop=asyncio.get_event_loop()

    try:
        result=await loop.run_in_executor(None,resize_image_cpu_bound,source_path,dest_path)
        JOBS[job_id]["files"][filename]={"status":"done",**result}

    except Exception as e:
        JOBS[job_id]["files"][filename]={"status":"failed","error":str(e)}

    statuses=[f["status"] for f in JOBS[job_id]["files"].values()]
    if all(s in ("done","failed") for s in statuses):
        JOBS[job_id]["status"]="compleleted"
        JOBS[job_id]["completed_at"]=datetime.now(timezone.utc).isoformat()

@app.post("/batch_upload")
async def batch_upload(background_tasks:BackgroundTasks,files:Annotated[List[UploadFile],File(...)]):
    job_id=str(uuid.uuid4())
    JOBS[job_id]={
        "status":"processing",
        "created_at":datetime.now(timezone.utc).isoformat(),
        "files":{},
    }
    for upload in files:
        contents=await upload.read()
        source_path = UPLOAD_DIR/upload.filename
        with open(source_path,"wb") as f:
            f.write(contents)

        JOBS[job_id]["files"][upload.filename]={"status":"queued"}

        background_tasks.add_task(process_single_image,job_id,upload.filename,source_path)

    return {"job_id":job_id,"file_count":len(files),"status":"processing"}

@app.get("/batch-status/{job_id}")
def get_batch_status(job_id:str):
    job=JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404,detail="Job not found")
    return job