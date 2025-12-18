import pytest

from app.node_server import ADMIN_SESSIONS, CANDIDATES, app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    ADMIN_SESSIONS.clear()
    CANDIDATES.clear()
    with app.test_client() as client:
        yield client
    ADMIN_SESSIONS.clear()
    CANDIDATES.clear()

def test_frontend_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Cast Your Vote' in response.data

# We skip full vote submit test here as it requires valid session token.
# But we can verify it rejects unverified users.
def test_frontend_submit_requires_session(client):
    response = client.post('/vote/submit', json={'candidate': 'Alice', 'private_key': 'test'})
    assert response.status_code == 401  # Session required

def test_admin_requires_auth(client):
    """Admin dashboard should redirect to login without auth."""
    response = client.get('/admin')
    assert response.status_code == 302  # Redirect to login

def test_admin_login_success(client):
    """Admin login works with correct password."""
    res = client.post('/admin/login', json={'password': 'admin123'})
    assert res.status_code == 200
    assert 'token' in res.json

def test_admin_login_failure(client):
    """Admin login fails with wrong password."""
    res = client.post('/admin/login', json={'password': 'wrongpassword'})
    assert res.status_code == 401

def test_admin_dashboard_with_auth(client):
    """Admin dashboard loads after authentication."""
    # Login first
    login_res = client.post('/admin/login', json={'password': 'admin123'})
    token = login_res.json['token']
    
    # Access admin with token in header
    response = client.get('/admin', headers={'X-Admin-Token': token})
    assert response.status_code == 200
    assert b'Admin Panel' in response.data

def test_candidates_api_requires_admin(client):
    """Adding candidate requires admin auth."""
    res = client.post('/candidates/add', json={'name': 'Alice'}, headers={'Accept': 'application/json'})
    assert res.status_code == 401

def test_candidates_api_with_auth(client):
    """Candidates API works with admin auth."""
    # Login
    login_res = client.post('/admin/login', json={'password': 'admin123'})
    token = login_res.json['token']
    
    # Add candidate
    res = client.post('/candidates/add', json={'name': 'Alice'}, headers={'X-Admin-Token': token})
    assert res.status_code == 201
    
    # Get list (no auth needed for read)
    res = client.get('/candidates')
    assert 'Alice' in res.json['candidates']

def test_stats_endpoint(client):
    res = client.get('/stats')
    assert res.status_code == 200
    assert 'chain_length' in res.json
    assert 'nodes_count' in res.json
    assert res.json['chain_length'] >= 1  # At least genesis block
