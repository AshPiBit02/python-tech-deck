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


