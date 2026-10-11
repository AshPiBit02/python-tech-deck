from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse

app=FastAPI(title="Send Stored File Back to the Client")

UPLOAD_DIR=Path("uploads").resolve()

@app.get("/files/{filename}")
async def download(filename:str):
    path=(UPLOAD_DIR/filename).resolve()
    if path.parent!=UPLOAD_DIR or not path.is_file():
        raise HTTPException(status_code=404,detail="File not found")
    return FileResponse(path,filename=path.name)