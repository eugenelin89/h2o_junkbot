# https://www.cloudamqp.com/docs/celery.html
import celery, os, requests, json, tasks, fb, states, apiai
from intents import *


#_post_msg_url = 'https://graph.facebook.com/v2.6/me/messages?access_token='+os.environ['FBOT_ACCESS_TOKEN']


app = celery.Celery('demo')
app.conf.update(
    BROKER_URL=os.environ['CLOUDAMQP_URL'],
    BROKER_POOL_LIMIT=20,
    BROKER_HEARTBEAT = None,
    CELERY_RESULT_BACKEND = None,
    CELERY_SEND_EVENTS = False,
    CELERY_EVENT_QUEUE_EXPIRES = 60)


@app.task
def fb_process(data):
    if 'message' in data['entry'][0]['messaging'][0]: # The 'messaging' array may contain multiple messages.  Need fix.
        sender_id = data['entry'][0]['messaging'][0]['sender']['id']
        message = data['entry'][0]['messaging'][0]['message']['text']
        nlp = apiai.query(sender_id, message)
        print json.dumps(nlp, indent = 4)
        return fb.send_message(sender_id, str(message))
    return

@app.task
def save_conversation(timestamp, sender_id, sender_msg, response_msg):
    print 'SAVE CONVERSATION...'
    # 1. store message to db by POST to baymax_firebase
    post_url = os.environ['POST_MSG_URL']
    print 'store_dialog, POST to ' + post_url
    data = {'timestamp':timestamp,'sender_id':sender_id, 'sender_msg':sender_msg, 'response_message':response_msg}
    requests.post(post_url, json=data)
    return

@app.task
def process_user_response(sender_id, intent, parameters):
    print('process_user_response(%s, %s, %s)'%(sender_id, intent, '{parameters}'))
    # test
    state = states.get_state(sender_id)

    if intent and intent in intents.keys():
        intents[intent](sender_id, parameters)
    else:
        intents['Fallback'](sender_id, parameters)
    return



###########
# Helpers #
###########

def collect_sender_info(sender_id):
    print 'actually collect sender info'
    profile = get_fb_profile(sender_id)
    first_name = profile['first_name']
    last_name = profile['last_name']
    print 'sender name: '+first_name+' '+last_name
    msg = first_name+' , what is the best way to contact you? Please provide us your contact preference and information?'
    fb.send_message(sender_id, msg)

    return
