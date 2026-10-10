from typing import List
from fastapi import FastAPI,File,UploadFile

app=FastAPI(title="Multiple File Upload")

@app.post("/upload/multiple")
async def upload_multiple(files:List[UploadFile]=File(...)):
    return [
        {"filename":f.filename,"content_type":f.content_type} for f in files
    ]

