"""
PROBLEM: It's tempting a register ONE handler for the bare 'Exception'
class to "handle everything" -- but this silently swallows genuine bugs
(typos, missing keys) behind a generic message, making them much harder
to notice and debug.

SOLUTION (shown via contrast): Keep a narrow, deliberate set of specific
exception types with their own handlers, and let truly unexpected errors
surface as FastAPI's normal unhandled 500 -- don't hide them behind a
catch-all.
"""

from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
app=FastAPI(title="Catch All Anit-pattern Exceptions Demo")

class KnownBusinessError(Exception):
    def __init__(self,reason:str):
        self.reason=reason

@app.exception_handler(KnownBusinessError)
async def handle_known_error(request:Request,exc:KnownBusinessError):
    return JSONResponse(status_code=400,content={"detail":exc.reason})

@app.get("/known-error")
def known_error_route():
    raise KnownBusinessError(reason="This is an expected, handled failure")

@app.get("/real-bug")
def real_bug_error():
    data={"name":"Toyota"}
    return data["naaaaame"] # delibrate