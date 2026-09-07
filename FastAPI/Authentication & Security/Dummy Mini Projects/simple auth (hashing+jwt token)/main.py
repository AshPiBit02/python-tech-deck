from fastapi import FastAPI,APIRouter,Depends,HTTPException
from .database import USERS
from .auth import hash_password

app=FastAPI()

@app.post("/register")
def register(email:str,password:str)->dict:
    if USERS[email]:
        raise HTTPException(status_code=400,detail="Email already in use!")
    hashed_passsword=hash_password(password)
    USERS["email"]=email
    USERS["password"]=hashed_passsword
    return {"message":f"New user {email} registered"}

@app.post("/token")



    
