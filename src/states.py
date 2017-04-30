import requests, json, actions, os, fb
from abc import ABCMeta, abstractmethod
from messages import *

class State(object):
    __metaclass__ = ABCMeta

    def __init__(self, sender_id):
        self.sender_id = sender_id
        pass

    def message_sender(self, response_messages):
        ''' takes a list of messages and will send in order '''
        for message in response_messages:
            fb.send_message(self.sender_id, message)
        return

    def set_next_state(self, next_state):
        print 'Setting next state to: '+ next_state
        url = os.environ['GET_STATE_URL']
        payload = {'state':next_state}
        requests.post(url, json = payload, params = {'sender_id':self.sender_id}).json()
        return

    @abstractmethod
    def responds_to_sender(self, sender_id, message, nlp_data):
        pass


class INIT(State):
    def responds_to_sender(self, sender_message, nlp_data):
        print 'INIT.responds_to_user'
        # 1. If smalltalk avail, reply with smalltalk
        action = nlp_data.get('result').get('action')
        if action.strip().find('smalltalk') == 0:
            self.message_sender([nlp_data.get("result").get("fulfillment").get("speech")])
        # 2. Say Hello
        self.message_sender([HELLO_MESSAGE_1, HELLO_MESSAGE_2])
        # 3. Prompt for ZIP
        self.message_sender([PROMPT_ZIP_MESSAGE])
        # 4. Change state to WAIT_FOR_ZIP
        result = self.set_next_state('WAIT_FOR_ZIP')
        return

class WAIT_FOR_ZIP(State):
    def responds_to_sender(self, sender_message, nlp_data):
        # 1. Extract ZIP Code. For now, assume whatever sent is the intended zip.
        # 2. Send to PIPELINE for verifcation
        self.message(['Current State is WAIT_FOR_ZIP'])

#################################
# Get Instance of a STATE object
#################################
def get_state(sender_id):
    url = os.environ['GET_STATE_URL']
    cur_state = requests.get(url, {'sender_id':sender_id}).json()
    state = None
    if cur_state == None or cur_state['state'] not in globals(): # user has not yet started
        state = INIT(sender_id)
    else:
        state_class = globals()[cur_state['state']]
        state = state_class(sender_id)
    return state
