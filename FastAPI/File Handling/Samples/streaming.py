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

@app.get("/export/csv")
async def export_csv():
    def rows():
        yield "id,name\n"
        for i in range(1,1001):
            yield f"{i},user_{i}\n"
    return StreamingResponse(rows(),media_type="text/csv",headers={"Content-Disposition":'attachment; filename="users.csv"'})