def test_list_users_as_admin(client,admin_headers,registered_user):
    response=client.get("/admin/users",headers=admin_headers)
    assert response.status_code==200
    emails=[u["email"] for u in response.json()]
    assert registered_user.email in emails

def test_list_users_as_regular_user_forbidden(client,auth_headers):
    response=client.get("/admin/users",headers=auth_headers)
    assert response.status_code==403

def test_list_users_no_token(client):
    response=client.get("/admin/users")
    assert response.status_code==401

def test_delete_user_as_admin(client,admin_headers,registered_user):
    response=client.delete(f"/admin/users/{registered_user.id}",headers=admin_headers)
    assert response.status_code==200

def test_delete_user_as_regular_user_forbidden(client,auth_headers,admin_user):
    response=client.delete(f"/admin/users/{admin_user.id}",headers=auth_headers)
    assert response.status_code==403

def test_delete_nonexistent_user_as_admin(client,admin_headers):
    response=client.delete(f"/admin/user/404",headers=admin_headers)
    assert response.status_code==404