import requests, json, os, re, dateutil.parser, datetime, pytz, bisect
import apiai, obe
from abc import ABCMeta, abstractmethod
from messages import *
from intents import *

MAX_TIME_SELECTIONS = 5

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

    @abstractmethod
    def responds_to_sender(self, sender_id, message, nlp_data, payload):
        pass

#####################
# Persistent States #
#####################
################################################################################
class INIT(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        print 'INIT.responds_to_user'
        # 1. If smalltalk avail, reply with smalltalk
        action = nlp_data.get('result').get('action')
        if action.strip().find('smalltalk') == 0:
            self.send_messages([nlp_data.get("result").get("fulfillment").get("speech")])
        # 2. Say Hello
        self.send_messages([HELLO_MESSAGE_1, HELLO_MESSAGE_2])
        # 3. Prompt for ZIP
        self.send_messages([PROMPT_ZIP_MESSAGE])
        # 4. Change state to WAIT_FOR_ZIP
        result = self.set_next_state('WAIT_FOR_ZIP')
        return

################################################################################
class WAIT_FOR_DETAIL(State):
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
            my_obe = obe.OBE()
            is_time_held = my_obe.hold_timeslot(service_id, start_time, finish_time)
            if is_time_held:
                # prompt for details PROMPT_DETAIL_MESSAGE
                self.send_messages([PROMPT_DETAIL_MESSAGE])
                # go to next state
                self.set_next_state('WAIT_FOR_DETAIL')
            else:
                # Something went wrong... Prompt user to call sales centre.
                # Set next state back to INIT
                self.send_messages([HOLD_TIME_FAILED])
                self.set_next_state('INIT')
        else:
            # ToDo: send the next few available times, prompt user again, and loop back to this state
            qr = []
            counter = 0
            for str_start_time in starts:
                ts = dateutil.parser.parse(str_start_time)
                counter = counter + 1
                title = ts.strftime("%a %b %d, %I:%M%p") # Wed May 03, 09:30AM
                qr.append({'content_type':'text', 'title':title, 'payload':str_start_time})
                if counter > MAX_TIME_SELECTIONS-1:
                    break
            self.send_messages([MORE_TIMESLOT], quick_reply=qr)
            self.set_next_state('WAIT_FOR_TIMESLOT')
            pass


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
        my_obe = obe.OBE()
        zip_verification = my_obe.is_zip_verified(zipcode.replace(' ',''))
        if zipcode and 'error' not in zip_verification.keys():
            # ZIPCODE VERIFIED
            franchise_id = zip_verification.get('franchise_id')
            self.update_order({'franchise_id':franchise_id})
            self.update_order({'zip':zipcode})
            self.send_messages([ZIP_RECEIVED % (zipcode)])
            # 1. Get availability,
            availabilities = my_obe.get_availabilities()
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
            self.set_next_state('INIT')
        else:
            # missing zipcode
            self.send_messages([MISSING_ZIP, PROMPT_ZIP_MESSAGE])
            self.set_next_state('WAIT_FOR_ZIP') # stay in this state
        return




####################
# Transient States #
####################
################################################################################
class ZIP_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

################################################################################
class TIMESLOT_SUBMITTED(State):
    def responds_to_sender(self, sender_message, nlp_data, payload = None):
        pass

#################################
# Get Instance of a STATE object
#################################
################################################################################
def get_state(sender_id):
    url = os.environ['GET_STATE_URL']
    cur_state = requests.get(url, {'sender_id':sender_id}).json()
    state = None

    if cur_state == None or cur_state not in globals(): # user has not yet started
        state = INIT(sender_id)
    else:
        state_class = globals()[cur_state]
        state = state_class(sender_id)
    return state
