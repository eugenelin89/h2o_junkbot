import os, requests, json, datetime

class CRM(object):
    def __init__(self):
        # OBE related detail should be encapsulated in the OBE object
        self.access_token = None
        self.instance_url = None
        self.franchise_id = None
        self.zipcode = None
        self.authenticated = False
        self.__authenticate()

    def execute_booking(self, booking_info):
        if not self.__authenticate():
            print 'OBE Authentication Error'
            return False

        # Step 1: Junk customer
        url = self.instance_url + os.environ['OBE_RESOURCE_PATH_JUNK_CUSTOMER']
        address = booking_info.get('address')
        to_address = '%s;%s;%s;%s;%s' % ( address.get('city'), address.get('country'), \
                                           address.get('state'), address.get('street'), \
                                           address.get('zip') )
        headers = {
            "Authorization":'Bearer '+self.access_token,
            'Content-Type':'application/json'
        }
        data = {
            'brand' : os.environ['OBE_BRAND'],
            'franchise_id' : booking_info.get('franchise_id'),
            'first_name' : booking_info.get('first_name'),
            'last_name' : booking_info.get('last_name'),
            'phone' : booking_info.get('phone'),
            'email' : booking_info.get('email'),
            'to_address' : to_address,
            'start_date_time' : booking_info.get('start_time'),
            'finish_date_time' : booking_info.get('finish_time'),
            'pickup_description' : booking_info.get('detail'),
            'additional_information_required' : 0
        }

        res = requests.post(url, json = data, headers = headers)
        if res.status_code != requests.codes.ok:
            print 'Error: ' + res.text
             return False
        junk_customer = res.json()
        service_type_id = junk_customer.get('service_type_id')
        recordowner_id = junk_customer.get('recordowner_id')
        recordowner_account_id = junk_customer.get('recordowner_account_id')
        opportunity_id = junk_customer.get('opportunity_id')
        globalnote_id = junk_customer.get('globalnote_id')
        contact_id = junk_customer.get('contact_id')
        account_id = junk_customer.get('account_id')
        print 'junk_customer: ' + json.dumps(junk_customer, indent = 4)

        # Step 2: Junk Service
        url2 = self.instance_url + os.environ['OBE_RESOURCE_PATH_JUNK_SERVICE']
        data2 = {
            'brand' : os.environ['OBE_BRAND'],
            'franchise_id' : booking_info.get('franchise_id'),
            'first_name' : booking_info.get('first_name'),
            'phone' : booking_info.get('phone'),
            'email' : booking_info.get('email'),
            'to_address' : to_address,
            'start_date_time' : booking_info.get('start_time'),
            'finish_date_time' : booking_info.get('finish_time'),
            'service_id' : booking_info.get('availabilities').get('serviceId'),
            'customer_type' : 'Residential',
            'notes' : 'Booked by Junkbot',
            'service_type_id' : service_type_id,
            'recordowner_id' : recordowner_id,
            'recordowner_account_id' : recordowner_account_id,
            'opportunity_id' : opportunity_id,
            'globalnote_id' : globalnote_id,
            'contact_id' : contact_id,
            'account_id' : account_id
        }
        res2 = requests.post(url2, json = data2, headers = headers)
        if res2.status_code != requests.codes.ok:
            print 'Error: ' + res2.text
            return False
        return True

    def is_zip_verified(self, zipcode):
        # Authenticate

        if not zipcode:
            return {'error':'zipcode is None'}

        if not self.__authenticate():
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
        if not self.__authenticate():
            return {'error':'OBE Authentication error'}
        url = self.instance_url + os.environ['OBE_RESOURCE_PATH_AVAILABILITY']
        start_date = datetime.date.today().isoformat()
        end_date = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        data = {
            'franchise_id' : self.franchise_id,
            'start_date' : start_date,
            'end_date' : end_date,
            'postal_code' : self.zipcode,
            'brand' : os.environ['OBE_BRAND']
        }
        headers = {
            'Authorization':'Bearer '+self.access_token,
            'Content-Type':'application/json; charset=utf-8'
        }
        res = requests.post(url, json = data, headers = headers)

        if res.status_code == requests.codes.ok and res.json().get('timeslots'):
            print 'availabilities returned'
            return res.json()
        else:
            print 'error occurred in get_availabilities: '+res.text
            return {'error':res.text}

    def hold_timeslot(self, service_id, start_time, finish_time):
        print 'hold_timeslot(%s, %s %s)'%(service_id, start_time, finish_time)
        if not self.__authenticate():
            return {'error':'OBE Authentication error'}
        url = self.instance_url + os.environ['OBE_RESOURCE_PATH_HOLD_SLOT']
        headers = {
            "Authorization":'Bearer '+self.access_token
        }
        data = {
            'service_id' : service_id,
            'start_date_time' : start_time,
            'finish_date_time' : finish_time,
        }
        res = requests.post(url, json = data, headers = headers)
        if res.status_code == requests.codes.ok and res.text.find('true') >= 0:
            print 'Hold time successful '
            return True
        else:
            print 'Failed to hold time ' + str(res.status_code) + ': '+res.text
            return False



    def __authenticate(self):
        print 'authenticate with OBE'
        if not self.authenticated:
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
                self.authenticated = True
        return self.authenticated
