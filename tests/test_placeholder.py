from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_list():
    response = client.get('/docs')
    assert response.status_code == 200