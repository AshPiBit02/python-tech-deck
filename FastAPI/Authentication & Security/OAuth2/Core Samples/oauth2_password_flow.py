from fastapi import Depends,HTTPException,Header,FastAPI
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from root_auth import hash_password,create_access_token,verify_password

app=FastAPI()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

USERS:dict[str,dict]={}

def get_user(user_id:str=Header(...),token:str=Depends(oauth2_scheme)):
    user=USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=400,detail=f"User with id {user_id} not registered")
    return user

@app.post("/register")
def register_user(email:str=Header(...),password:str=Header(...),role:str=Header(...)):
    for user in USERS.values():
        if user["email"]==email:
            raise HTTPException(status_code=400,detail="Email already registered")
    user_id=f"user{len(USERS)+1}"
    hashed_password=hash_password(password)
    USERS[user_id]={"email":email,"password":hashed_password,"role":role}
    return {"message":f"User {user_id} registered"}

@app.post("/token")
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user = next((u for u in USERS.values() if u["email"]==form_data.username),None)
    if user is None or not verify_password(form_data.password,user["password"]):
        raise HTTPException(status_code=401,detail="Invalid email or password")
    access_token=create_access_token({"sub":user["email"]})
    return {"access_token":access_token,"token_type":"bearer"}

@app.get("/me")
def get_me(user:dict=Depends(get_user)):
    return user

    


