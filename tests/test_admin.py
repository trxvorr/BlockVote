import json

import pytest

from app.admin_server import app, initialize_keys


@pytest.fixture
def client():
    app.config['TESTING'] = True
    initialize_keys()
    with app.test_client() as client:
        yield client

def test_get_key(client):
    response = client.get('/admin/key')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'public_key' in data
    assert 'BEGIN RSA PUBLIC KEY' in data['public_key']

def test_sign_blindly_success(client):
    # Simulate a voter request
    payload = {
        'voter_id': 'voter_123',
        'blinded_hash': 1234567890  # Mock blinded integer
    }
    response = client.post('/admin/sign', json=payload)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'blind_signature' in data
    assert isinstance(data['blind_signature'], int)

def test_double_signing_prevention(client):
    payload = {
        'voter_id': 'voter_double',
        'blinded_hash': 11111
    }
    # First sign should succeed
    response = client.post('/admin/sign', json=payload)
    assert response.status_code == 201
    
    # Second sign should fail
    response = client.post('/admin/sign', json=payload)
    assert response.status_code == 403
    assert b'Voter has already obtained a signature' in response.data

def test_missing_fields(client):
    payload = {'voter_id': 'only_id'}
    response = client.post('/admin/sign', json=payload)
    assert response.status_code == 400
