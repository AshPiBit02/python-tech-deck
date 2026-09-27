"""
include_in_schema=False: A feature that allows some routes to be hidden from common users.
"""
from fastapi import FastAPI

app=FastAPI(title="Include in Schema Demo")

@app.get("/users/{user_id}")
def get_user_by_id(user_id:int):
    return {"user_id":user_id,"type":"general"}

@app.get("/about")
def get_info():
    return {"details":"This API demonstrate the hidding of internal routes from common users."}

@app.get("/internal/health",include_in_schema=False)
def health():
    return {"status":"OK"}

@app.get("/internal/stats",include_in_schema=False)
def stats():
    return {"active user":36}
