import os, requests, json, datetime

class OBE(object):
    def __init__(self):
        # OBE related detail should be encapsulated in the OBE object
        self.access_token = None
        self.instance_url = None
        self.franchise_id = None
        self.zipcode = None

    def is_zip_verified(self, zipcode):
        # Authenticate

        if not zipcode:
            return {'error':'zipcode is None'}
        is_authenticated = self.__authenticate()
        if not is_authenticated:
            return {'error':'OBE Authentication error'}

        url = self.instance_url + os.environ['OBE_RESOURCE_PATH_VERIFY_AREA']
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
            self.franchise_id = res.json().get('franchise_id')
            self.zipcode = zipcode
            return res.json()
        else:
            return {'error':'zipcode cannot be verified'}

    def get_availabilities(self):
        print 'get_availability()'
        url = self.instance_url + os.environ['OBE_RESOURCE_PATH_AVAILABILITY']
        start_date = datetime.date.today().isoformat()
        end_date = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        data = {
            'franchise_id' : self.franchise_id,
            #'start_date' : start_date,
            #'end_date' : end_date,
            #'postal_code' : self.zipcode,
            #'brand' : os.environ['OBE_BRAND']
        }
        headers = {
            'Authorization':'Bearer '+self.access_token,
            'Content-Type':'application/json'
        }
        print url
        print json.dumps(data, indent=4)
        print json.dumps(headers, indent=4)

        res = requests.post(url, data=data, headers=headers)
        if res.status_code == requests.codes.ok and res.json().get('timeslots'):
            print 'availabilities returned'
            return res.json()
        else:
            print 'error occurred in get_availabilities: '+res.text
            return {'error':res.text}

    def __authenticate(self):
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
