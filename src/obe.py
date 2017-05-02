import os, requests, json

class OBE(object):
    def __init__(self):
        self.access_token = None
        self.instance_url = None

    def is_zip_verified(self, zipcode):
        # Authenticate

        if not zipcode:
            return {'error':'zipcode is None'}
        is_authenticated = self.authenticate()
        if not is_authenticated:
            return {'error':'OBE Authentication error'}

        url = self.instance_url + os.environ['OBE_RESOURCE_PATH']
        headers = {
            "Authorization":'Bearer '+self.access_token
        }
        params = {
            'from_postal_code':zipcode,
            'brand':os.environ['OBE_BRAND']
        }
        res = requests.get(url, params = params, headers = headers)
        print 'verify_zip result: '+ res.text
        if res.status_code == requests.codes.ok:
            return res.json()
        else:
            return {'error':'zipcode cannot be verified'}

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
