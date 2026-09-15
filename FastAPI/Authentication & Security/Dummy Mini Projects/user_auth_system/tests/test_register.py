from core.config import settings

def test_register_success(client):
    response=client.post("/register",json={
        "email":"dummy@gmail.com",
        "password":"dumbTheWise",
        "confirm_password":"dumbTheWise",
    })
    assert response.status_code==200
    body=response.json()
    assert body["email"]=="dummy@gmail.com"
    assert body["role"]=="User"
    assert "hashed_password" not in body

def test_register_duplicate_email(client):
    payload={
        "email":"notdummy@gmail.com",
        "password":"jaldiTheLate",
        "confirm_password":"jaldiTheLate",
    }
    client.post("/register",json=payload)
    response=client.post("/register",json=payload)
    assert response.status_code==400
    assert "already registered" in response.json()["detail"]

def test_register_password_mismatch(client):
    response=client.post("/register",json={
        "email":"aegon@gmail.com",
        "password":"aegonTheV",
        "confirm_password":"jonSnowNoV",
    })
    assert response.status_code==400
    assert "do not match" in response.json()["detail"]

def test_register_weak_password(client):
    response=client.post("/register",json={
        "email":"eddar@gmail.com",
        "password":"ned",
        "confirm_password":"ned",
    })
    assert response.status_code==422

def test_register_admin_without_key(client):
    respone=client.post("/register",json={
        "email":"fakeadmin@gmail.com",
        "password":"dummypassword",
        "confirm_password":"dummypassword",
        "role":"Admin",
    })
    assert respone.status_code==422

def test_register_admin_with_wrong_key(client):
    response=client.post("/register",json={
        "email":"imposteradmin@gmail.com",
        "password":"maybecorrect",
        "confirm_password":"maybecorrect",
        "role":"Admin",
        "admin_secret_key":"wrongadminkey",
    })
    assert response.status_code==403

def test_register_admin_with_correct_key(client):
    response=client.post("/register",json={
        "email":"genuineadmin@gmail.com",
        "password":"validpassword",
        "confirm_password":"validpassword",
        "role":"Admin",
        "admin_secret_key":settings.admin_secret_key,
    })
    assert response.status_code==200
    assert response.json()["role"]=="Admin"
