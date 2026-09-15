def test_login_success(client,registerd_user):
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

    
