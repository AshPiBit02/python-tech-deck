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
