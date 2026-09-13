from fastapi import FastAPI
from routers import auth,users

app=FastAPI(title="User Auth System")

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/about")
def about():
    return {"description":"A JWT + RBAC based user authentication system built with FastAPI and PostgreSQL."}