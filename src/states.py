import requests, json
from abc import ABCMeta, abstractmethod

class ABCState(object):
    __metaclass__ = ABCMeta


class INIT(ABCState):
    def __init__(self):
        state = "init"

class WAIT_FOR_ZIP(ABCState):
    pass


def get_state(sender_id):
    url = os.environ['GET_STATE_URL']
    cur_state = requests.get(url, {'sender_id':sender_id}).json()
    state = None
    if current_state == None or cur_state['state'] not in globals(): # user has not yet started
        state = INIT()
    else:
        state_class = globals()[cur_state['state']]
        state = state_class()
    return state
