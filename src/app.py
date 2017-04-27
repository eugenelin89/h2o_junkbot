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


#######################
# Inbound from API.AI #
#######################

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))
    res = processRequest(req)
    res = json.dumps(res, indent=4)
    #print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
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


def debug(message):
    print(message, file=sys.stderr)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
