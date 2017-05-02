import os, requests

def is_zip_verified(zip_code):
    # Authenticate
    verified = False
    auth = authenticate()
    if auth['error']:
        return verified
    access_token = auth['access_token']
    instance_url = auth['instance_url']
    url = instance_url + os.environ['OBE_RESOURCE_PATH']
    headers = {
        "Authorization":'Bearer '+access_token
    }
    params = {
        'from_postal_code':zip_code
        'brand':os.environ['OBE_BRAND']
    }
    res = requests.get(url, params = params, headers = headers)
    print 'verify_zip result: '+ res.text
    if res.status_code == requests.codes.ok:
        verified = True
    return verified




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
