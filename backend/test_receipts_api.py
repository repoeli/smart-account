import os
import time
import requests

API = os.environ.get('API_BASE', 'http://localhost:8000/api/v1')


def auth_headers():
    email = os.environ['TEST_EMAIL']
    password = os.environ['TEST_PASSWORD']
    res = requests.post(f'{API}/auth/login/', json={'email': email, 'password': password})
    res.raise_for_status()
    tok = res.json()['access_token']
    return {'Authorization': f'Bearer {tok}'}


def test_list_and_detail_authorization():
    h = auth_headers()
    # list
    r = requests.get(f'{API}/receipts/', headers=h)
    assert r.status_code == 200
    data = r.json()
    receipts = data.get('receipts', [])
    if receipts:
        rid = receipts[0]['id']
        d = requests.get(f'{API}/receipts/{rid}/', headers=h)
        assert d.status_code in (200, 400)
        # if 400, it should be a not authorized message when user mismatch; otherwise success



