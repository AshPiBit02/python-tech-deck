"""
PROBLEM: A client uploads a large file (video, DB dump, etc.) via a
raw POST body. If you declare it as 'bytes' or even 'UploadFile' in
some flows, FastAPI/Starlette may buffer the whole thing in memory 
first. For multi-GB uploads that risks OOM-killing your process.

SOLUTION: Use 'request.stream()' to read the body in chunks directly
from the ASGI connection and write each chunk straight to disk, keeping
memory usage flat regardless of file size.
"""

import uuid
from fastapi import FastAPI,Request

app=FastAPI(title="Streaming Large Upload Demo")

UPLOAD_DIR="/tmp/uploads"

@app.post("/upload-raw")
async def upload_raw(request:Request):
    import os
    os.makedirs(UPLOAD_DIR,exist_ok=True)
    file_id=str(uuid.uuid4())
    dest_path=os.path.join(UPLOAD_DIR,file_id)

    total_bytes=0
    with open(dest_path,"wb") as f:
        async for chunk in request.stream():
            f.write(chunk)
            total_bytes+=len(chunk)

    return {"file_id":file_id,"bytes_received":total_bytes,"path":dest_path}