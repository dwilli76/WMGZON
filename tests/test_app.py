from tests.conftest import client

def test_index_route(client):
    """
    GIVEN flask app
    WHEN GET request to '/index' page
    THEN check page loads without error
    """
    response = client.get('/index', follow_redirects=True)
    assert response.status_code == 200

def test_404_handler(client):
    """
    GIVEN flask app
    WHEN GET request to unknown page
    THEN check page returns 404 error
    """
    response = client.get('/not_a_real_page', follow_redirects=True)
    assert response.status_code == 404

def test_unauth_admin_route(client):
    """
    GIVEN flask app with no authenticated user
    WHEN GET request to login_required page
    THEN check page redirects to '/login'
    """
    response = client.get('/categories/technology/manage', follow_redirects=True)
    assert response.request.path == "/login/"

def test_login_post_incorrect_details(client):
    """
    GIVEN invalid login details
    WHEN POST request to '/login' route
    THEN check page redirects to '/login' with status 400
    """
    response = client.post('login', data={
        "email": "admin@wmgzon.com",
        "pword": "Incorrect"
    }, follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == "/login/"

def test_login_post_correct_details(client):
    """
    GIVEN valid login details
    WHEN POST request to '/login' route
    THEN check page redirects to '/home' with status 200
    """
    response = client.post('login', data={
        "email": "admin@wmgzon.com",
        "pword": "Admin123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/home/"

def test_add_to_basket(client):
    """
    GIVEN flask app and product ID
    WHEN POST request to '/basket' route
    THEN check page redirects to '/basket' with status 200
    """
    response = client.post('/basket', data={
        "productID": "1",
        "productOptions": "Blue"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/basket/"

