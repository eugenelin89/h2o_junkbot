from __future__ import print_function
from flask import Flask, request, make_response, abort, logging
import urllib, json, os, sys, requests, tasks
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

@app.route("/health_check", methods=['GET'])
def health_check():
    url = os.environ['BASE_URL']
    res = requests.get(url)
    return res.json()


#########################
# Inbound from Facebook #
#########################
@app.route("/fb_webhook/<bot_id>", methods=['GET'])
def handshake(bot_id):
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == os.environ['VERIFY_TOKEN'] and challenge != None: # need fix
        return challenge
    else:
        abort(401)

@app.route("/fb_webhook/<bot_id>", methods=['POST'])
def process_message(bot_id):
    # received message from user
    data = request.json # type dict, whereas request.data is type str
    tasks.fb_process.delay(data)
    return "ok"

#######################
# Inbound from API.AI #
#######################

@app.route('/webhook', methods=['POST'])
def webhook():
    ''' Deprecating '''
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))
    processRequest(req)
    res = json.dumps(res, indent=4)
    #print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    ''' Deprecating '''
    # Get incoming message
    print('processRequest...')
    sender_id = req.get("originalRequest").get("data").get("sender").get("id")
    sender_msg = req.get("originalRequest").get("data").get("message").get("text")
    response_msg = req.get("result").get("fulfillment").get("speech")
    timestamp = req.get("timestamp")
    action = req.get("result").get("action")
    intent = req.get("result").get("metadata").get("intentName")
    parameters = req.get("result").get("parameters")
    tasks.save_conversation.delay(timestamp, sender_id, sender_msg, response_msg)
    tasks.process_user_response.delay(sender_id, intent, parameters)
    return



###########
# Helpers #
###########

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
