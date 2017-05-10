import requests, json, os, re, dateutil.parser, datetime, pytz, bisect, usaddress, time
import apiai, crm, fb
from abc import ABCMeta, abstractmethod
from messages import *
from intents import *

MAX_TIME_SELECTIONS = 5
MAX_WAIT_SECONDS = 15 * 60

class State(object):
    __metaclass__ = ABCMeta

    def __init__(self, sender_id):
        self.sender_id = sender_id

    def send_messages(self, response_messages, quick_reply = None, buttons = None):
        ''' takes a list of messages and will send in order '''
        for message in response_messages:
            fb.send_message(self.sender_id, message, quick_reply = quick_reply, buttons = buttons)
        return

    def set_next_state(self, next_state):
        print 'Setting next state to: '+ next_state
        url = os.environ['GET_STATE_URL']
        payload = {'state':next_state}
        res = requests.post(url, json = payload, params = {'sender_id':self.sender_id})
        if res.status_code == requests.codes.ok:
            apiai.set_context(self.sender_id, next_state)
        return

    def update_order(self, payload):
        # sample payload: {'franchise_id':franchise_id}
        url = os.environ['ORDER_URL']
        res = requests.post(url, json = payload, params = {'sender_id':self.sender_id})
        return

    def get_order_with_key(self, key):
        url = os.environ['ORDER_URL']
        res = requests.get(url, params = {'sender_id':self.sender_id, 'key':key}).json()
        return res

    def archive(self):
        booking = requests.get(os.environ['CONFIRM_URL'], {'sender_id' : self.sender_id}).json()
        url = os.environ['ARCHIVE_URL']
        res = requests.post(url, json=booking, params = {'sender_id':self.sender_id})
        requests.delete(os.environ['ORDER_URL'], params = {'sender_id':self.sender_id})

    @abstractmethod
    def responds_to_sender(self, sender_id, message, nlp_data, payload):
        pass

    @abstractmethod
    def _next_state(self):
        pass

#####################
# Persistent States #
#####################
################################################################################
class INIT(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        # ToDo: time stamp
        print 'INIT.responds_to_user'
        # 0. timestamp
        self.update_order({'timestamp':time.time()})
        # 1. If smalltalk avail, reply with smalltalk
        action = nlp_data.get('result').get('action')
        if action.strip().find('smalltalk') == 0:
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech")])
        # 2. Say Hello
        self.send_messages([HELLO_MESSAGE_1, HELLO_MESSAGE_2])
        # 3. Prompt for ZIP
        self.send_messages([PROMPT_ZIP_MESSAGE])
        # 4. Get first_name and last_name
        profile = fb.get_fb_profile(self.sender_id)
        print json.dumps(profile, indent=4)
        self.update_order({'first_name':profile.get('first_name')})
        self.update_order({'last_name':profile.get('last_name')})

        # 5. Change state to WAIT_FOR_ZIP
        result = self.set_next_state('WAIT_FOR_ZIP')
        return

    # ToDo: Refactor state transition here
    def _next_state(self):
        pass
################################################################################
class RESET(State):
    def __init__(self, sender_id):
        super(RESET, self).__init__(sender_id)
        print 'RESET STATE instantiated'
        # DELETE order for sender_id
        self.set_next_state('RESET')
        self.archive()
        #requests.delete(os.environ['ORDER_URL'], params = {'sender_id':self.sender_id})
        #self.set_next_state('INIT')

    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    # ToDo: Refactor state transition here
    def _next_state(self):
        pass

################################################################################
class WAIT_FOR_CONFIRMATION(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('CONFIRMATION_SUBMITTED')
        # Anything senders sent will be recorded.
        if nlp_data.get('result').get('action').strip().find('smalltalk') == 0:
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech")])
            qr = [{'content_type':'text', 'title':BOOK_JOB, 'payload':'BOOK_JOB'},{'content_type':'text', 'title':CANCEL, 'payload':'CANCEL'}]
            self.send_messages([PROCEED], quick_reply=qr)
            self.set_next_state('WAIT_FOR_CONFIRMATION')
            return
        if nlp_data.get('result').get('metadata').get('intentName') == CONFIRM_INTENT:
            print 'Proceed to Booking...'
            is_booked = self.__book_appointment()
            if is_booked:
                self.send_messages([IS_CONFIRMED])
                # Archive Order
                self.set_next_state('BOOKED')
                self.archive()
                # Delete Order
                #requests.delete(os.environ['ORDER_URL'], params = {'sender_id':self.sender_id})
            else:
                # Ask sener to call support
                self.send_messages([BOOKING_FAILED])
                # Archive Order
                self.set_next_state('BOOKING_FAILED')
                self.archive()
                # DELETE order for sender_id
                #requests.delete(os.environ['ORDER_URL'], params = {'sender_id':self.sender_id})

        elif nlp_data.get('result').get('metadata').get('intentName') == CANCEL_INTENT:
            print 'Cancel Booking...'
            self.set_next_state('CANCELLED')
            self.archive()
            #requests.delete(os.environ['ORDER_URL'], params = {'sender_id':self.sender_id})
            self.send_messages([BYE])
        else:
            qr = [{'content_type':'text', 'title':BOOK_JOB, 'payload':'BOOK_JOB'},{'content_type':'text', 'title':CANCEL, 'payload':'CANCEL'}]
            self.send_messages([PROCEED], quick_reply=qr)
            self.set_next_state('WAIT_FOR_CONFIRMATION')


    def __book_appointment(self):
        booking_info = requests.get(os.environ['CONFIRM_URL'], {'sender_id' : self.sender_id}).json()
        my_crm = crm.CRM()
        return my_crm.execute_booking(booking_info)


    # ToDo: Refactor state transition here
    def _next_state(self):
        pass


################################################################################
class WAIT_FOR_EMAIL(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('EMAIL_SUBMITTED')
        if nlp_data.get('result').get('action').strip().find('smalltalk') == 0:
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech")])
            self.set_next_state('WAIT_FOR_EMAIL')
            return
        pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        p = re.compile(pattern)
        emails = p.findall(sender_message)
        if not len(emails):
            print 'Invalid Email'
            self.sender_message(SEND_EMAIL)
            self.set_next_state('WAIT_FOR_EMAIL')
            return
        print 'valid Email'
        email = emails[0]
        self.update_order({'email':email})
        self._next_state()

    def _next_state(self):
        # Getting confirmation info
        res = requests.get(os.environ['CONFIRM_URL'], {'sender_id' : self.sender_id}).json()
        self.send_messages([self.__format_confirmation(res)])
        qr = [{'content_type':'text', 'title':BOOK_JOB, 'payload':'BOOK_JOB'},{'content_type':'text', 'title':CANCEL, 'payload':'CANCEL'}]
        self.send_messages([PROCEED], quick_reply=qr)
        self.set_next_state('WAIT_FOR_CONFIRMATION') # Debug

    def __format_confirmation(self, order):
        # Name
        name = order.get('first_name') + ' ' + order.get('last_name')
        # Phone
        phone = order.get('phone')

        # EMail
        email = order.get('email')

        # Address
        address = '%s %s, %s, %s, %s'  % (order.get('address').get('street'), \
                         order.get('address').get('city'), \
                         order.get('address').get('state'), \
                         order.get('address').get('country'), \
                         order.get('address').get('zip') )
        # Appointment time
        appointment_time  = dateutil.parser.parse(order.get('start_time')).strftime("%a %b %d, %I:%M%p") # Wed May 03, 09:30AM

        # Details
        details = order.get('detail').replace(' -|- ','\n')
        return 'Name: %s\nPhone: %s\nEmail: %s\nAddress: %s\nAppointment: %s\nDetails:\n%s' % (name, phone, email, address, appointment_time, details)


################################################################################
class WAIT_FOR_PHONE(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('PHONE_SUBMITTED')
        if nlp_data.get('result').get('action').strip().find('smalltalk') == 0:
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech"), SEND_PHONE_NUMBER])
            self.set_next_state('WAIT_FOR_PHONE')
            return
        pattern = r'\D*([2-9]\d{2})(\D*)([2-9]\d{2})(\D*)(\d{4})\D*'
        p = re.compile(pattern)
        phone_segments = p.findall(sender_message)
        if not len(phone_segments):
            # prompt the sender for phone number again
            print 'Invalid Phone Number'
            self.send_messages([SEND_PHONE_NUMBER])
            self.set_next_state('WAIT_FOR_PHONE')
            return
        print 'Valid Phone Number'
        phone = ''
        for segment in list(phone_segments[0]):
            print segment
            phone = phone + segment
        self.update_order({'phone':phone})
        self._next_state()

    def _next_state(self):
        # Prompt for Email
        self.send_messages([SEND_EMAIL])
        self.set_next_state('WAIT_FOR_EMAIL')
        pass

################################################################################
class WAIT_FOR_ADDRESS(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('ADDRESS_SUBMITTED')
        if nlp_data.get('result').get('action').strip().find('smalltalk') == 0:
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech"), SEND_ADDRESS_AGAIN])
            self.set_next_state('WAIT_FOR_ADDRESS')
            return
        address = self.parse_address(sender_message.upper())
        print json.dumps(address, indent=4)
        if not address.get('zip'):
            # Get it from Firebase
            zip = self.get_order_with_key('zip')
            address['zip'] = zip
            print 'zip: ' + str(zip)
            print 'found zip!' + json.dumps(address, indent=4)
        if not address.get('country'):
            # determine US or Canada based on the zip
            pattern = '[ABCEGHJKLMNPRSTVXY][0-9][ABCEGHJKLMNPRSTVWXYZ][0-9][ABCEGHJKLMNPRSTVWXYZ][0-9]'
            p = re.compile(pattern)
            r = p.search(address['zip'].upper().replace(' ',''))
            if r:
                address['country'] = 'Canada'
            else:
                address['country'] = 'United States'
        print json.dumps(address, indent = 4)
        if not address.get('city') or not address.get('state') or not address.get('street'):
            msg = MISSING_ADDRESS_INFO
            if not address.get('street'):
                msg =  msg + '\nStreet Address'
            if not address.get('city'):
                msg = msg + '\nCity'
            if not address.get('state'):
                msg = msg + '\nState/Province'
            msg = msg + '\n'+SEND_ADDRESS_AGAIN
            self.send_messages([msg])
            self.set_next_state('WAIT_FOR_ADDRESS')
            return
        # Save address info in Firebase, and proceed.
        self.update_order({'address':address})
        self.send_messages([SEND_PHONE_NUMBER])
        self.set_next_state('WAIT_FOR_PHONE')


    def parse_address(self, input_str):
        address = usaddress.tag(input_str)
        print json.dumps(address, indent=4)
        print type(address)
        # compose street
        street = ''
        if 'OccupancyType' in address[0].keys() and 'OccupancyIdentifier' in address[0].keys():
            street = '%s %s, '% (address[0].get('OccupancyType'), address[0].get('OccupancyIdentifier'))
        if not address[0].get('AddressNumber') or not address[0].get('StreetName'):
            street = None
        elif not address[0].get('StreetNamePostType'):
            street = street + '%s %s' % (address[0].get('AddressNumber'), address[0].get('StreetName'))
        else:
            street = street + '%s %s %s' % (address[0].get('AddressNumber'), address[0].get('StreetName'), address[0].get('StreetNamePostType'))
        result = {
            'city':address[0].get('PlaceName'),
            'country':address[0].get('CountryName'),
            'state':address[0].get('StateName'),
            'street':street.upper(),
            'zip':address[0].get('ZipCode')
        }
        return result

    # ToDo: Refactor state transition here
    def _next_state(self):
        pass

################################################################################
class WAIT_FOR_DETAIL(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('DETAIL_SUBMITTED')


        intent = nlp_data.get('result').get('metadata').get('intentName')
        # Anything senders sent will be recorded.
        if intent == DETAIL_DONE_INTENT:
            # move to the next intent
            print 'OK, FINISHED GETTING DETAILS!'
            self.send_messages([ASK_FOR_ADDRESS])
            self.set_next_state('WAIT_FOR_ADDRESS')
            return
        qr = [{'content_type':'text', 'title':DONE, 'payload':DONE}]
        self.send_messages([ASK_IF_DONE_DETAILS], quick_reply = qr)
        # Get current detail and add onto it
        url = os.environ['DETAIL_URL']
        detail = requests.get(url, {'sender_id':self.sender_id}).json()
        if not detail:
            detail = sender_message
        else:
            detail = detail + ' -|- ' + sender_message
        # save it.
        payload = {'detail':detail}
        res = requests.post(url, json = payload, params = {'sender_id':self.sender_id})
        self.set_next_state('WAIT_FOR_DETAIL')

    # ToDo: Refactor state transition here
    def _next_state(self):
        pass

################################################################################
class WAIT_FOR_TIMESLOT(State):
    def __init__(self, sender_id):
        super(WAIT_FOR_TIMESLOT, self).__init__(sender_id)
        self.availabilities = None

    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('TIMESLOT_SUBMITTED')
        timeslot = None
        if payload:
            # Sender clicked on quick_reply. We can trust and use directly.
            # example {"payload": "2017-05-03T16:00:00.000Z"}
            timeslot = payload.get('payload')
        else:
            # Parse sender's input
            intent = nlp_data.get('result').get('metadata').get('intentName')
            if intent == TIMESLOT_INTENT:
                date_string = nlp_data.get('result').get('parameters').get('date')
                time_string = nlp_data.get('result').get('parameters').get('time')
                # format above to the accepted datetime string
                timeslot = self.__datetime_string(date_string, time_string)
            elif nlp_data.get('result').get('action').strip().find('smalltalk') == 0:
                # small talk back
                self.send_messages([nlp_data.get("result").get("fulfillment").get("speech")])
        # timeslot still None, that means we didn't get timeslot from user.
        if timeslot == None:
            # Todo: 1. Get the available selection from Firebase.
            # Todo: 2. Request again with the available timeslots in step 1.
            qr = []
            counter = 0
            for timeslot in self.__get_availabilities().get("timeslots"):
                ts = dateutil.parser.parse(timeslot.get('start'))
                start_time = timeslot.get('start')
                finish_time = timeslot.get('finish')
                counter = counter + 1
                title = ts.strftime("%a %b %d, %I:%M%p") # Wed May 03, 09:30AM
                qr.append({'content_type':'text', 'title':title, 'payload':timeslot.get('start')})
                if counter > MAX_TIME_SELECTIONS-1:
                    break
            self.send_messages([REPEAT_TIMESLOT], quick_reply=qr)
            self.set_next_state('WAIT_FOR_TIMESLOT')
            return
        # By getting to here, we have a timeslot string.
        # Check this to be an available timeslot from Firebase
        availabilities = self.__get_availabilities().get("timeslots")
        # list of start times in datetime.datetime
        starts = [dateutil.parser.parse(availabilities[i].get('start')) for i in range(len(availabilities)) ]
        timeslot_datetime = dateutil.parser.parse(timeslot)
        # position of timeslot if found, else index of first time slot that is larger
        pos = bisect.bisect_left(starts, timeslot_datetime)
        print 'position '+ str(pos)
        if pos >= len(starts): # sender seleted time bigger than all starting time. So we list backwards
            starts = starts[len(starts)::-1]
        else: # include only times bigger or equal to sender selected time.
            starts = starts[pos:]
        if starts[0] and starts[0] == timeslot_datetime:
            # user selected available timeslot, hold the time
            # if hold is successful, go to next state.
            # if hold is unsuccessful, ask user to call in and set back to INIT state
            # pos still holds the index of the *original* starts which is in same order as availabilities
            start_time = availabilities[pos].get('start')
            finish_time = availabilities[pos].get('finish')
            service_id = timezone = self.__get_availabilities().get("serviceId")
            print 'start: '+start_time+' finish: '+finish_time
            self.send_messages([GIVE_FEW_SECONDS])
            my_crm = crm.CRM()
            is_time_held = my_crm.hold_timeslot(service_id, start_time, finish_time)
            if is_time_held:
                # Save the timeslot info in Firebase
                self.update_order({'start_time':start_time})
                self.update_order({'finish_time':finish_time})
                # prompt for details PROMPT_DETAIL_MESSAGE
                self.send_messages([PROMPT_DETAIL_MESSAGE])
                # go to next state
                self.set_next_state('WAIT_FOR_DETAIL')
                #self.set_next_state('RESET') # FOR DEBUGGING !!!
            else:
                # Something went wrong... Prompt user to call sales centre.
                # Set next state back to INIT
                self.send_messages([HOLD_TIME_FAILED])
                self.set_next_state('INIT')
        else:
            # Sender selected a time not in the available timeslots.
            # ToDo: Refactor the following code for reuse
            qr = []
            counter = 0
            for start_time in starts:
                counter = counter + 1
                title = start_time.strftime("%a %b %d, %I:%M%p") # Wed May 03, 09:30AM
                qr.append({'content_type':'text', 'title':title, 'payload':start_time.isoformat()})
                if counter > MAX_TIME_SELECTIONS-1:
                    break
            self.send_messages([MORE_TIMESLOT], quick_reply=qr)
            self.set_next_state('WAIT_FOR_TIMESLOT')


    def __get_timeslot(datetime_str):
        pass

    def __datetime_string(self, date_string, time_string):
        # date_string: "2017-05-05" Missing string means today.
        # time_sring: "16:00:00"
        # our datetime string looks like: 2017-05-06T16:30:00.000Z
        # Note: Interpretation of today/tomorrow etc appear based on Eastern time
        # Tricky thing is that when sender types in a time he intends local time.
        # Lets forget about timezone for now...
        if not date_string:
            timezone = self.__get_availabilities().get("time_zone")
            tz = pytz.timezone(timezone)
            date_string = str(datetime.datetime.now(tz).date())
        if not time_string:
            # NOT suppose to happen...
            time_string = '00:00:00'
        return '%sT%s.00Z' % (date_string, time_string)


    def __get_availabilities(self):
        if not self.availabilities:
            self.availabilities = requests.get(os.environ['GET_AVAIL_URL'], {'sender_id':self.sender_id}).json()
        return self.availabilities

    # ToDo: Refactor state transition here
    def _next_state(self):
        pass

################################################################################
class WAIT_FOR_ZIP(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        self.set_next_state('ZIP_SUBMITTED') # TRANSIENT STATE
        zipcode = ""
        intent = nlp_data.get('result').get('metadata').get('intentName')
        # Zipcode Intent
        if intent == ZIPCODE_INTENT:
            print 'ZIP found by ZIPCODE_INTENT'
            zipcode = nlp_data.get('result').get('parameters').get('zip-code')
        # Sender small-talking
        elif nlp_data.get('result').get('action').strip().find('smalltalk') == 0:
            # smalltalk back
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech")])
        # User sent stand-alone zipcode
        else:
            # try search for zipcode in sender_message
            print 'Matching ZIP based on regex...'
            pattern = r'(\d{5}(-\d{4})?$)|([ABCEGHJKLMNPRSTVXY]{1}\d{1}[A-Z]{1} *\d{1}[A-Z]{1}\d{1}$)'
            p = re.compile(pattern)
            r = p.search(sender_message.upper())
            if r:
                zipcode = r.group()
        # If zipcode extracted, send for verification
        # Else, propmpt for zipcode again.
        # ToDo: What about area not serviced?
        my_crm = crm.CRM()
        zip_verification = my_crm.is_zip_verified(zipcode.replace(' ',''))
        if zipcode and 'error' not in zip_verification.keys():
            # ZIPCODE VERIFIED
            franchise_id = zip_verification.get('franchise_id')
            self.update_order({'franchise_id':franchise_id})
            self.update_order({'zip':zipcode.upper()})
            self.send_messages([ZIP_RECEIVED % (zipcode)])
            # 1. Get availability,
            availabilities = my_crm.get_availabilities()
            qr = []
            if 'error' not in availabilities.keys():
                counter = 0
                service_id = availabilities.get('serviceId')
                #self.update_order({'service_id':service_id})
                self.update_order({'availabilities':availabilities})
                for timeslot in availabilities.get('timeslots'):
                    ts = dateutil.parser.parse(timeslot.get('start'))
                    start_time = timeslot.get('start')
                    finish_time = timeslot.get('finish')
                    counter = counter + 1
                    title = ts.strftime("%a %b %d, %I:%M%p") # Wed May 03, 09:30AM
                    qr.append({'content_type':'text', 'title':title, 'payload':timeslot.get('start')})
                    if counter > MAX_TIME_SELECTIONS-1:
                        break
                print str(qr)
                self.send_messages([SELECT_TIMESLOT], quick_reply=qr)
                self.set_next_state('WAIT_FOR_TIMESLOT')
            # 2. Send users availabilities for selection,
            # 3. Move to the next state WAIT_FOR_SELECTION
        elif zipcode:
            # ZIPCODE was extracted but could not be verified.
            # Should ask sender to contact customer support
            print 'ZIPCODE cannot be verified: '+zipcode
            self.send_messages([UNVERFIABLE_ZIP])
            self.set_next_state('INVALID_ZIP')
            self.archive()
        else:
            # missing zipcode
            self.send_messages([MISSING_ZIP, PROMPT_ZIP_MESSAGE])
            self.set_next_state('WAIT_FOR_ZIP') # stay in this state
        return

    # ToDo: Refactor state transition here
    def _next_state(self):
        pass


####################
# Transient States #
####################
################################################################################
class CONFIRMATION_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

################################################################################
class EMAIL_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

################################################################################
class PHONE_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

################################################################################
class ADDRESS_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

################################################################################
class ZIP_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

################################################################################
class TIMESLOT_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

################################################################################
class DETAIL_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

    def _next_state(self):
        pass

#################################
# Get Instance of a STATE object
#################################
################################################################################
def get_state(sender_id):
    # ToDo: If timestamp is over x minutes ago, regardless state,
    # re-start from INIT

    # get timestamp from order. if +15 min ago, start over
    timestamp = requests.get(os.environ['ORDER_URL'], params = {'sender_id':sender_id, 'key':'timestamp'}).json()
    if timestamp:
        curstamp = time.time()
        if (curstamp - timestamp) > MAX_WAIT_SECONDS:
            # Update state to EXPIRED
            #url = os.environ['GET_STATE_URL']
            #payload = {'state':'EXPIRED'}
            #res = requests.post(url, json = payload, params = {'sender_id':sender_id})
            # Archive the previous order
            #booking = requests.get(os.environ['CONFIRM_URL'], {'sender_id' : sender_id}).json()
            #url = os.environ['ARCHIVE_URL']
            #res = requests.post(url, json=booking, params = {'sender_id': sender_id})
            # Delete the previous order
            #requests.delete(os.environ['ORDER_URL'], params = {'sender_id': sender_id})
            RESET(sender_id)


    url = os.environ['GET_STATE_URL']
    cur_state = requests.get(url, {'sender_id':sender_id}).json()
    state = None

    if cur_state == None or cur_state not in globals(): # user has not yet started
        state = INIT(sender_id)
    else:
        state_class = globals()[cur_state]
        state = state_class(sender_id)
    return state
