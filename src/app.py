from __future__ import print_function
from flask import Flask, request, abort, logging
import os, sys, requests, tasks
# _access_token and _post_msg_url will eventually be moved to another module/process for sending messages.

#########
# Setup #
#########
app = Flask(__name__)

#########
# Flask #
#########

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    abort(401)

@app.route("/test", methods=['GET'])
def test():
    tasks.add.delay(1,2)
    return "Good Test!"


@app.route("/fb_webhook/<bot_id>", methods=['GET'])
def handshake(bot_id):
    debug('Hello FooBar!')
    debug(request.data)
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == os.environ['VERIFY_TOKEN'] and challenge != None: # need fix
        return challenge
    else:
        abort(401)

import requests
_post_msg_url = 'https://graph.facebook.com/v2.6/me/messages?access_token='+os.environ['FBOT_ACCESS_TOKEN']
test = 0
def testfunc(data):
    global test
    test = test + 1
    sender_id = data['entry'][0]['messaging'][0]['sender']['id']
    resp_data = {
        "recipient" : {"id":sender_id},
        "message" : {"text":"TEST -> "+str(test)}        
    }
    post_result = requests.post(_post_msg_url, json=resp_data)
    return post_result

@app.route("/fb_webhook/<bot_id>", methods=['POST'])
def process_message(bot_id):
    # received message from user
    debug('Process message...\n'+request.data)
    data = request.json # type dict, whereas request.data is type str
    tasks.process.delay(data)
    return "ok"


###########
# Helpers #
###########


def debug(message):
    print(message, file=sys.stderr)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
