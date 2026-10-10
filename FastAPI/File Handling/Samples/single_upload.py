from fastapi import FastAPI,File,UploadFile

app=FastAPI(title="Single File Upload")

@app.post("/upload")
async def upload(file:UploadFile=File(...)):
    content=await file.read()
    return {"filename":file.filename,"content_type":file.content_type,"size":len(content)}
