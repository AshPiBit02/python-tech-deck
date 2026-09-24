from fastapi import FastAPI

app=FastAPI()

@app.middleware("http")
async def say_hello(request,call_next):
    print("A request just arrived!")
    response=await call_next(request)
    print("A response is about to be sent back!")
    return response

@app.get("/")
def home():
    return {"message":"Halo boss"}