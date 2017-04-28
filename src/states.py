import requests, json, actions, os
from abc import ABCMeta, abstractmethod

class State(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def execute_intent(sender_id, intent, parameters):
        pass


class INIT(State):
    def execute_intent(sender_id, intent, parameters):
        # Say Hello

        # Prompt user

        # Update State
        pass

class WAIT_FOR_ZIP(State):
    def execute_intent(sender_id, intent, parameters):
        pass

#################################
# Get Instance of a STATE object
#################################
def get_state(sender_id):
    url = os.environ['GET_STATE_URL']
    cur_state = requests.get(url, {'sender_id':sender_id}).json()
    state = None
    if cur_state == None or cur_state['state'] not in globals(): # user has not yet started
        state = INIT()
    else:
        state_class = globals()[cur_state['state']]
        state = state_class()
    return state
