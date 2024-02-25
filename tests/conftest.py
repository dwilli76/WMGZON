import pytest
from app import app

@pytest.fixture
def app():
    app.config.update({"TESTING": True})
    yield app

    @pytest.fixture
    def client(app):
        return app.test_client()