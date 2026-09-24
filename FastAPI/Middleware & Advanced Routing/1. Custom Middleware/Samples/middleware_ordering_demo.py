from fastapi import FastAPI

app=FastAPI()

@app.middleware("http")
async def middleware_a(request,call_next):
    print("A: before")
    response=await call_next(request)
    print("A: after")
    return response

@app.middleware("http")
async def middleware_b(request,call_next):
    print("B: before")
    response=await call_next(request)
    print("B: after")
    return response