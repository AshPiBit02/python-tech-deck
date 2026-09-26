"""
PROBLEM: A full app requires a real database connection and a real auth
service to even start up. Writing a test for one small router shouldn't
require booting all of that.

SOLUTION: Mount just the router to be test on a throwaway FastAPI() instance,
and use app.dependency_overrides to replace real dependencies(DB session, 
current user) with fakes - no real DB or auth server to run the test.
"""
from typing import Annotated
from fastapi import APIRouter,FastAPI,Depends
from fastapi.testclient import TestClient

def get_db():
    raise RuntimeError("Real DB connection - should never be called in this test!")

def get_current_username(db=Depends(get_db))->str:
    return db.lookup_current_user()

router=APIRouter(prefix="/profile")

@router.get("/")
def read_profile(username:Annotated[str,Depends(get_current_username)]):
    return {"username":username,"profile_complete":True}

test_app=FastAPI()
test_app.include_router(router)

# test_app.dependency_overrides[get_current_username]=lambda:"fake-test-user" ## Shorthand

def get_fake_user():
    return "fake-test-user"

test_app.dependency_overrides[get_current_username]=get_fake_user

client=TestClient(test_app)

def test_read_profile_uses_fake_user():
    response=client.get("/profile/")
    assert response.status_code==200
    assert response.json()=={"username":"fake-test-user","profile_complete":True}