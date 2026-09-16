def test_get_me_success(client,auth_headers,registered_user):
    response=client.get("/me",headers=auth_headers)
    assert response.status_code==200
    body=response.json()
    assert body["email"]==registered_user.email
    assert body["role"]=="User"

def test_get_me_no_token(client):
    response=client.get("/me")
    assert response.status_code==401

def test_get_me_invalid_token(client):
    response=client.get("/me",headers={"Authorization":"Bearer garbage.token.value"})
    assert response.status_code==401

def test_update_me_email(client,auth_headers):
    response=client.patch("/me",headers=auth_headers,json={"email":"newemail@gmail.com"})
    print(response.json())
    assert response.status_code==200
    assert response.json()["email"]=="newemail@gmail.com"

def test_update_me_password(client,auth_headers,registered_user,db_session):
    response=client.patch("/me",headers=auth_headers,json={"password":"newstrongpass123"})
    assert response.status_code==200

def test_update_me_role_upgrade_wrong_key(client,auth_headers):
    response=client.patch("/me",headers=auth_headers,json={"role":"Admin","admin_secret_key":"wrongKey"})
    assert response.status_code==403

def test_update_me_role_upgrade_correct_key(client,auth_headers,registered_user):
    from core.config import settings
    response=client.patch("/me",headers=auth_headers,json={"role":"Admin","admin_secret_key":settings.admin_secret_key})
    assert response.status_code==200
    assert response.json()["role"]=="Admin"

