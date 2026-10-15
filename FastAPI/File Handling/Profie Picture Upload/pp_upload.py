from fastapi import FastAPI,UploadFile,HTTPException,File

app=FastAPI(title="Profile Picture Upload")

ALLOWED_TYPES={"image/png","image/png"}

@app.post("/users/{id}/avatar")
async def update_profile(id:str,avatar:UploadFile=File(...)):
    if avatar.content_type not in ALLOWED_TYPES:
        raise HTTPException(415,"Unsupported Media Type")

    head=await avatar.read(8)
    if not (head.startswith(b"\xff\xd8\xff") or head.startswith(b"\x89PNG\r\xla\n")):
        raise HTTPException(415,"Unsupported Media Type")

   

    

