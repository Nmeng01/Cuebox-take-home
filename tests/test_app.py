import pytest
import io
from web_app.app import create_app

@pytest.fixture
def app():
    """Created app instance"""
    app = create_app()
    app.config["TESTING"] = True

    yield app

@pytest.fixture
def client(app):
    """Returned client for test usage"""
    return app.test_client()

def test_ping(client):
    """Ensure main page is running"""
    response =  client.get("/")
    assert response.status_code == 200

def test_get_outputs():
    return