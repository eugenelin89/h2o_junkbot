import fb, requests, os
# output action of intentions

def intention_func1(sender_id, parameters):
    print 'intention_func1'
    data = {}
    # at this layer, should be platform agnostic.
    # send msg back to user
    msg = 'jf1 rocks! '
    resp_data = {"id":sender_id,"message":msg} #
    #res = requests.post(os.environ['JFACE_URL'], json=resp_data)
    fb.send_message(sender_id, msg)
    return res

def begin_dialog(sender_id, parameters):
    print 'begin_dialog'
    return
