from fastapi import FastAPI

app=FastAPI()

@app.middleware("http")
async def add_security_headers(request,call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Strict-Transport-Security"]="max-age=3607200"
    return response