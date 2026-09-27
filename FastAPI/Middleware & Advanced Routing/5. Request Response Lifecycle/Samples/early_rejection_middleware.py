"""
Problem: A public API gets hit by requets from known abusive IPs. If the ban check
happens inside a dependency (after a DB session is already open), every rejected
request still wastes a real DB connection before being refused.

Solution: Do the check in middleware, BEFORE dependency resolution even begins, so
a rejected request costs almost nothing.
"""

from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import JSONResponse

app=FastAPI(title="Early Rejection Middleware Demo")

BANNED_IPS={"203.0.113.7","198.51.100.23"}

@app.middleware("http")
async def block_banned_ips(request,call_next):
    if request.client.host in BANNED_IPS:
        return JSONResponse(status_code=403,content={"detail":"Access denied"})
    return await call_next(request)

def get_fake_db():
    print("Opening a (fake) DB connection...")
    yield {"notes":["Buy groceries","Call Jhonny: The plumber"]}
    print("Closing the (fake) DB connection...")

@app.get("/notes")
def read_notes(db:dict=Depends(get_fake_db)):
    return {"notes":db["notes"]}