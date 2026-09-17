from fastapi import FastAPI
import time

app=FastAPI()
@app.get("/sync-blocking")
def sync_blocking_route():
    time.sleep(5) # only blocks ITS OWN thread
    return {"status":"done"}

@app.get("/fast")
def fast_route():
    return {"status":"instant"}