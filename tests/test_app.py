from tests.conftest import client

def test_status_code_ok(client):
    response = client.get('/index')
    assert response.status_code == 200



