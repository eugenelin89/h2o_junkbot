import fb, requests, os, json
# output action of intentions

def fallback_action(sender_id, parameters):
    print 'intention_func1'
    data = {}
    # at this layer, should be platform agnostic.
    # send msg back to user
    msg = 'foobar rocks!'
    resp_data = {"id":sender_id,"message":msg} #
    #res = requests.post(os.environ['JFACE_URL'], json=resp_data)
    res = fb.send_message(sender_id, msg)
    return res

def begin_action(sender_id, parameters):
    print('begin_dialog(%s, %s, %s)' % (sender_id , json.dumps(parameters, indent=4)))
    # get profile, if no profile, set profile
    # check which step ware are currently on, as well as timestamp

    return {}

def zip_submit(sender_id, parameters):
    pass

def timeslot_submit(sender_id, parameters):
    pass

def detail_submit(sender_id, parameters):
    pass

def address_submit(sender_id, parameters):
    pass
