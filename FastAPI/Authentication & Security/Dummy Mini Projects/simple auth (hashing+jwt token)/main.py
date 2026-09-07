from fastapi import FastAPI,APIRouter,Depends,HTTPException
from database import USERS
from auth import hash_password,verify_password,create_access_token

app=FastAPI()

@app.post("/register")
def register(email:str,password:str)->dict:
    if email in USERS:
        raise HTTPException(status_code=400,detail="Email already in use!")
    hashed_passsword=hash_password(password)
    USERS[email]={"email":email,"password":hashed_passsword}
    return {"message":f"New user {email} registered"}

@app.post("/login")
def login(email:str,password:str):
    if not USERS[email]:
        raise HTTPException(status_code=401,detail=f"Invalid username, register first")
    
    if not verify_password(password,USERS[email]["password"]):
        raise HTTPException(status_code=401,detail=f"Incorrect password!")
    
    access_token=create_access_token({"sub":email})
    return {"access_token":access_token,"token_type":"bearer"}
    

