import pytest

from app.node_server import OTP_STORE, VERIFIED_SESSIONS, app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Clear stores before each test
    OTP_STORE.clear()
    VERIFIED_SESSIONS.clear()
    with app.test_client() as client:
        yield client
    # Clean up after
    OTP_STORE.clear()
    VERIFIED_SESSIONS.clear()

def test_request_otp(client):
    res = client.post('/auth/request-otp', json={'email': 'test@example.com'})
    assert res.status_code == 200
    assert 'test@example.com' in OTP_STORE
    assert len(OTP_STORE['test@example.com']['otp']) == 6

def test_verify_otp_success(client):
    # First request OTP
    client.post('/auth/request-otp', json={'email': 'test@example.com'})
    otp = OTP_STORE['test@example.com']['otp']
    
    # Verify
    res = client.post('/auth/verify-otp', json={'email': 'test@example.com', 'otp': otp})
    assert res.status_code == 200
    assert 'session_token' in res.json
    assert res.json['session_token'] in VERIFIED_SESSIONS

def test_verify_otp_invalid(client):
    client.post('/auth/request-otp', json={'email': 'test@example.com'})
    
    res = client.post('/auth/verify-otp', json={'email': 'test@example.com', 'otp': '000000'})
    assert res.status_code == 400
    assert 'Invalid OTP' in res.json['message']

def test_vote_requires_session(client):
    # Try to vote without session
    res = client.post('/vote/submit', json={
        'candidate': 'Alice',
        'private_key': 'fake',
        'election_id': 'default'
    })
    assert res.status_code == 401
    assert 'verify your email' in res.json['message']
