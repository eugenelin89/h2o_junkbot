import requests, json, actions, os, fb
from abc import ABCMeta, abstractmethod

class State(object):
    __metaclass__ = ABCMeta

    def __init__(self, sender_id):
        self.sender_id = sender_id
        pass

    def message_sender(self, response_message):
        return fb.send_message(self.sender_id, response_message)


    @abstractmethod
    def responds_to_sender(self, sender_id, message, nlp_data):
        pass


class INIT(State):
    def responds_to_sender(self, sender_message, nlp_data):
        print 'INIT.responds_to_user'
        # 1. If smalltalk avail, reply with smalltalk
        action = nlp_data.get('result').get('action')
        if action.strip().find('smalltalk') == 0:
            #smalltalk_resp = nlp_data.get("result").get("fulfillment").get("speech")
            self.message_sender(nlp_data.get("result").get("fulfillment").get("speech"))
        # 2. Say Hello
        # 3. Prompt for ZIP
        return

class WAIT_FOR_ZIP(State):

        pass

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
