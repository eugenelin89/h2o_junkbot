import os, requests

def verify_zip(zip_code):
    # Authenticate
    auth = authenticate()
    if auth['error']:
        return
    access_token = auth['access_token']
    instance_url = auth['instance_url']

    instance_url + os.environ['OBE_RESOURCE_PATH']

    headers = {
        "Authorization":'Bearer '+access_token
    }

    data = {
        'from_postal_code':zip_code
        'brand':os.environ['OBE_BRAND']
    }



    # Get result from OBE

def authenticate():
    url = os.environ['OBE_AUTH_URL']
    data = {
    'grant_type':'password',
    'client_id': os.environ['OBE_CLIENT_ID'],
    'client_secret': os.environ['OBE_CLIENT_SECRET'],
    'username': os.environ['OBE_USERNAME'],
    'password': os.environ['OBE_PASSWORD']
    }

    return requests.post(url, data=data).json()
