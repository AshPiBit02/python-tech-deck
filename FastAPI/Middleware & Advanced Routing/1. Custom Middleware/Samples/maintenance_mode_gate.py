from fastapi import FastAPI
import json

from fastapi.responses import JSONResponse
app=FastAPI()

MAINTENANCE_MODE=False

@app.middleware("http")
async def maintenance_gate(request,call_next):
    if MAINTENANCE_MODE and request.url.path!="/health":
        return JSONResponse(
            status_code=503,
            content={"detail":"Service temporarily unavilable for maintenance"},
        )
    return await call_next(request)