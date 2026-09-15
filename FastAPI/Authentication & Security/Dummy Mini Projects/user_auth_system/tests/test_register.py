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
    assert body["hashed_password"] not in body

def test_register_duplicate_email(client):
    payload={
        "email":"notdummy@gmail.com",
        "password":"jaldiTheLate",
        "confirm_password":"jaldiTheLate",
    }
    client.post("/register",json=payload)
    response=client.post("/register",json=payload)
    assert response.status_code==400
    assert "already registerd" in response.json()["detail"]

