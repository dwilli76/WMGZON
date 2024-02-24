def test_user_login(client):
    res = client.post(
        "login", data={
            "email": "admin@wmgzon.com",
            "password": "admin"},follow_redirects=True)
    assert res.status_code == 200
    assert res.request.path == "/"
    with client.session_transaction() as session:
        assert session["email"] == "admin@wmgzon.com"
