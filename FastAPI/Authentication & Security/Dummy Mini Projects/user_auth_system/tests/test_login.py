def test_login_success(client,registered_user):
    response=client.post("/token",data={
        "username":"testuser@gmail.com",
        "password":"strongpass",
    })
    assert response.status_code==200
    body=response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"]=="bearer"

def test_login_wrong_password(client,registered_user):
    response=client.post("/token",data={
        "username":"testuser@gmail.com",
        "password":"wrongpassword",

    })
    assert response.status_code==401


def test_login_nonexistent_user(client):
    response=client.post("/token",data={
        "username":"unknown@gmail.com",
        "password":"nomatterwhat",
    })
    assert response.status_code==401

def test_login_token_has_correct_claims(client,registered_user):
    from jose import jwt  
    from core.config import settings

    reponse=client.post("/token",data={
        "username":"testuser@gmail.com",
        "password":"strongpass",
    })
    access_token=reponse.json()["access_token"]
    payload=jwt.decode(access_token,settings.secret_key,algorithms=[settings.algorithm])

    assert payload["type"]=="access"
    assert payload["sub"]==str(registered_user.id)
    assert payload["role"]=="User"