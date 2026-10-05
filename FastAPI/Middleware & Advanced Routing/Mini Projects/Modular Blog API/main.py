from fastapi import FastAPI
from middleware import RequestLoggingMiddleware
from routers import comments,posts,users

app=FastAPI(title="Modular Blog API")

app.add_middleware(RequestLoggingMiddleware)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)

@app.get("/",tags=["Meta"])
def root():
    return {"message":"Modular Blog API is running!"}