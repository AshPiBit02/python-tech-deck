from fastapi import Depends,HTTPException,Header,FastAPI
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from root_auth import hash_password,create_access_token,verify_password,decode_access_token

app=FastAPI()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

USERS:dict[str,dict]={}

def get_user(token:str=Depends(oauth2_scheme)):
    payload=decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401,detail="Invalid or expired token")
    user_id=next(id for id,user in USERS.items() if user["email"]==payload.get("sub"))
    info=USERS[user_id]["about"]
    return {"user_id":user_id,"email":payload.get("sub"),"role":payload.get("role"),"about":info}

def get_users_list(current_user:dict=Depends(get_user)):
    if current_user["role"]!="admin":
        raise HTTPException(status_code=403,detail="Access Denied")
    return {uid: {k:v for k,v in u.items() if k!="password"} for uid, u in USERS.items()}

@app.post("/register")
def register_user(email:str=Header(...),password:str=Header(...),confirm_password:str=Header(...),role:str=Header(...),about:str|None=None):
    if password!=confirm_password:
        raise HTTPException(status_code=400,detail="Password didn't match")
    for user in USERS.values():
        if user["email"]==email:
            raise HTTPException(status_code=400,detail="Email already registered")
    user_id=f"user{len(USERS)+1}"
    hashed_password=hash_password(password)
    USERS[user_id]={"email":email,"password":hashed_password,"role":role,"about":about}
    return {"message":f"User {user_id} registered"}

@app.post("/token")
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user = next((u for u in USERS.values() if u["email"]==form_data.username),None)
    if user is None or not verify_password(form_data.password,user["password"]):
        raise HTTPException(status_code=401,detail="Invalid email or password")
    access_token=create_access_token({"sub":user["email"],"role":user["role"]})
    return {"access_token":access_token,"token_type":"bearer"}

@app.get("/me")
def get_me(user:dict=Depends(get_user)):
    return user

@app.get("/user/list")
def get_users_list(users:dict=Depends(get_users_list)):
    return users
