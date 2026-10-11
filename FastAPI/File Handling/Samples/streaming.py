from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import StreamingResponse

app=FastAPI(title="Streaming")
UPLOAD_DIR=Path("uploads").resolve()

@app.get("/stream/{filename}")
async def stream_file(filename:str):
    path=(UPLOAD_DIR/filename).resolve()
    if path.parent!=UPLOAD_DIR or not path.is_file():
        raise HTTPException(404,"File not found")

    def chunks():
        with path.open("rb") as f:
            while chunk:=f.read(1024*1024):
                yield chunk
    return StreamingResponse(chunks(),media_type="application/octet-stream")

