from fastapi import FastAPI,Depends,HTTPException,Security
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm,SecurityScopes
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone

app=FastAPI()
SECRET_KEY="dummy"
ALGORITHM="HS256"

oauth2_scheme=OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "notes:read":"View notes",
        "notes:write":"Create notes",
        "notes:delete":"Delete notes",
        "notes:admin":"Full control over notes",
    },
    )

SCOPE_HIERARCHY={
    "notes:admin":["notes:read","notes:write","notes:delete"],
}

FAKE_USERS={
    "viewer":{"password":"pass","allowed_scopes":["notes:read"]},
    "boss":{"password":"pass","allowed_scopes":["notes:admin"]},
}

NOTES={
    "1":"Buy electronics",
    "2":"Practice NM",
}

def expand_scopes(scopes:list[str])->list[str]:
    expanded=set(scopes)
    for scope in scopes:
        expanded.update(SCOPE_HIERARCHY.get(scope,[]))
    return list(expanded)

def create_token(username:str,scopes:list[str]):
    payload={"sub":username,"scopes":expand_scopes(scopes),"exp":datetime.now(timezone.utc)+timedelta(minutes=30)}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

@app.post("/token")
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user=FAKE_USERS.get(form_data.username)
    if not user or user["password"]!=form_data.password:
        raise HTTPException(status_code=401,detail="Invalid credentials")

    requested=form_data.scopes
    granted=[s for s in requested if s in user["allowed_scopes"]]
    denied=[s for s in requested if s not in user["allowed_scopes"]]
    token=create_token(form_data.username,granted)
    return {
        "access_token":token,
        "token_type":"bearer",
        "granted_scopes":granted,
        "denied_scopes":denied,
        "denied_reasons":{s:f"not permitted for {user}" for s in denied},
        }

def get_current_user(security_scopes:SecurityScopes,token:str=Depends(oauth2_scheme)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid or expired token")

    token_scopes=payload.get("scopes",[])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403,detail=f"Missing scope {scope}")
    return payload["sub"]

@app.get("/notes")
def read_notes(user:str=Security(get_current_user,scopes=["notes:read"])):
    return {"user":user,"notes":NOTES}

@app.post("/notes")
def create_notes(note:str,user:str=Security(get_current_user,scopes=["notes:write"])):
    note_id=f"{len(NOTES)+1}"
    NOTES[note_id]=note
    return {"user":user,"created":note_id}

@app.put("/notes/{note_id}")
def replace_note(note_id:str,note:str,password:str,user:str=Security(get_current_user,scopes=["notes:read","notes:write"])):
    if FAKE_USERS[user]["password"]!=password:
        raise HTTPException(status_code=403,detail="Incorrect password. Note replacement failed!")
    NOTES[note_id]=note
    return {"user":user,"replaced":note_id}

@app.delete("/notes/{note_id}")
def delete_note(note_id:str,password:str,user:str=Security(get_current_user,scopes=["notes:delete"])):
    if FAKE_USERS[user]["password"]!=password:
        raise HTTPException(status_code=403,detail="Incorrect password. Note deletion failed!")
    NOTES.pop(note_id,None)
    return {"user":user,"deleted":note_id}


