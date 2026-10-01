"""
PROBLEM: FastAPI's default validation error response is detailed and
developer-oriented -- fine for internal tools, but a public-facing API
may want a simpler, friendlier error shape for external clients.

SOLUTION: Register a handler for RequestValidationError specifically,
overriding FastAPI's own default handler for that exact same type.
"""

from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel,EmailStr,Field

app=FastAPI(title="Override Validation Error DEMO")

@app.exception_handler(RequestValidationError)
async def custom_validation_handler(request:Request,exc:RequestValidationError):
    simplified=[{"field":err["loc"][-1],"message":err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"detail":"Please check your input","erros":simplified}
    )

class RegisterRequest(BaseModel):
    email:EmailStr
    age:int=Field(...,gt=17)

@app.post("/register")
def register(body:RegisterRequest):
    return {"message":f"Registered {body.email}"}