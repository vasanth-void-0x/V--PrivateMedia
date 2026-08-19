from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_register_validation():
    response = client.post('/auth/register', json={'name':'A','username':'x','phone':'100','password':'123'})
    assert response.status_code == 400
