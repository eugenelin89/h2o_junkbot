import os, requests, json

class OBE(object):
    def __init__(self):
        self.access_token = None
        self.instance_url = None

    def is_zip_verified(self, zip_code):
        # Authenticate
        is_verified = False
        if not zip_code:
            return False
        is_authenticated = self.authenticate()
        if not is_authenticated:
            return False

        url = self.instance_url + os.environ['OBE_RESOURCE_PATH']
        headers = {
            "Authorization":'Bearer '+self.access_token
        }
        params = {
            'from_postal_code':zip_code,
            'brand':os.environ['OBE_BRAND']
        }
        res = requests.get(url, params = params, headers = headers)
        print 'verify_zip result: '+ res.text
        if res.status_code == requests.codes.ok:
            is_verified = True
        return is_verified

    def authenticate(self):
        print 'authenticate with OBE'
        result = False
        url = os.environ['OBE_AUTH_URL']
        data = {
            'grant_type':'password',
            'client_id': os.environ['OBE_CLIENT_ID'],
            'client_secret': os.environ['OBE_CLIENT_SECRET'],
            'username': os.environ['OBE_USERNAME'],
            'password': os.environ['OBE_PASSWORD']
        }
        res_json = requests.post(url, data=data).json()
        print 'authenticate result: ' + json.dumps(res_json, indent = 4)
        if 'access_token' in res_json.keys() and 'instance_url' in res_json.keys():
            self.access_token = res_json.get('access_token')
            self.instance_url = res_json.get('instance_url')
            result = True
        return result
