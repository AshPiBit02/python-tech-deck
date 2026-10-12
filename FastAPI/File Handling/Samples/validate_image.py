from fastapi import FastAPI,File,HTTPException,UploadFile

app=FastAPI(title="Image Validation")

ALLOWED={"image/jpeg","image/png"}

@app.post("/upload/image")
async def upload_image(file:UploadFile=File(...)):
    if file.content_type not in ALLOWED:
        raise HTTPException(415,"Only image/png or image/jpeg allowed")

    head=await file.read(8)
    if not (head.startswith(b"\xff\xd8\xff") or head.startswith("b\x89PNG\r\x1a\n")):
        raise HTTPException(415,"File content is not a real JPEG/PNG")
    return {"filename":file.filename,"valid":True}
                                