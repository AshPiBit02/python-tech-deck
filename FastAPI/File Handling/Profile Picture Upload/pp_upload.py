from fastapi import FastAPI,UploadFile,HTTPException,File
from pathlib import Path
from fastapi.responses import FileResponse

app=FastAPI(title="Profile Picture Upload")

ALLOWED_TYPES={"image/png","image/png"}
AVATAR_DIR=Path("avatars")
AVATAR_DIR.mkdir(exist_ok=True)

@app.post("/users/{id}/avatar")
async def update_profile(id:str,avatar:UploadFile=File(...)):
    if avatar.content_type not in ALLOWED_TYPES:
        raise HTTPException(415,"Unsupported Media Type")

    head=await avatar.read(8)
    if not (head.startswith(b"\xff\xd8\xff") or head.startswith(b"\x89PNG\r\n\x1a\n")):
        raise HTTPException(415,"Unsupported Media Type")

    await avatar.seek(0)

    profile=await avatar.read()
    if len(profile)>2*1024*1024:
        raise HTTPException(413,"File too large (max 2 MB)")

    dest=AVATAR_DIR/f"avtr{id}.png"
    with dest.open("wb") as f:
        f.write(profile)
    return {"message":"Profile uploaded successfully","saved_as":dest.name}


@app.get("/users/{id}/avatar")
async def get_profile(id:str):
    path=(AVATAR_DIR/f"avtr{id}.png").resolve()
    if not path.is_file():
        raise HTTPException(404,"Avatar not found")
    return FileResponse(path,filename=path.name)