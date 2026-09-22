import asyncio
import io
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path

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

