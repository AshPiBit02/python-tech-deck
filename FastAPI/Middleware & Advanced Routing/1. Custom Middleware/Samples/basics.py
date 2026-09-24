from fastapi import FastAPI
import time

app=FastAPI()


"""
@app.middleware("http")
async def say_hello(request,call_next):
    print("A request just arrived!")
    response=await call_next(request)
    print("A response is about to be sent back!")
    return response
"""
"""
request_count=0
@app.middleware("http")
async def count_requests(request,call_next):
    global request_count
    request_count+=1
    print(f"This is request number {request_count}")
    response=await call_next(request)
    return response

"""
"""
@app.middleware("http")
async def print_route_info(request,call_next):
    print(f"Someone requested: Method:{request.method} | Path:{request.url.path}")
    response = await call_next(request)
    return response
"""

@app.middleware("http")
async def show_timing(request,call_next):
    start_time=time.time()

    response=await call_next(request)

    duration=time.time()-start_time
    print(f"That request took {duration:.4f}s")
    return response

@app.get("/")
def home():
    return {"message":"Halo boss"}

@app.get("/about")
def about():
    return {"message":"This is for basic demonstration"}