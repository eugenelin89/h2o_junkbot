import os, requests, json

def send_message(sender_id, message, quick_reply = None, buttons = None):
    post_msg_url = os.environ['FB_GRAPHAPI_URL']+'me/messages'
    resp_data = {
        "recipient":{"id":sender_id},
        "message":{"text":message}
    }
    if quick_reply:
        resp_data["message"]["quick_replies"] = quick_reply
    if buttons:
        resp_data["message"]["buttons"] = buttons

    params = {'access_token': os.environ['FB_ACCESS_TOKEN']}
    print 'send following to Facebook: '
    print json.dumps(resp_data, indent = 4)
    res = requests.post(post_msg_url, params = params, json=resp_data)
    return res

def get_profile(sender_id):
    url = os.environ['FB_GRAPHAPI_URL']+sender_id
    params = {'fields':'first_name,last_name,profile_pic,locale,timezone,gender',
    'access_token':os.environ['FB_ACCESS_TOKEN']}
    # For local testing:
    #url = 'https://graph.facebook.com/v2.6/'+sender_id
    #params = {'fields':'first_name,last_name,profile_pic,locale,timezone,gender',
    #'access_token':'EAAaZCTAZBYPfoBAF0ZC9ZBfZCCfzEHfBeOZAxU9u0PvQIWt6D3JxfBE4PaKEVelakJ8A45LkhTn802mhSiD3YvvjZAEdw2584QOZCLXhns9rqFTVZCc2SYgqcXK7JwjR394J2dZCrt6xhMfVsZBPpIIDCr5x8laKHElTUsgYj3luZBpJMwZDZD'}

    res = requests.get(url, params).json()
    return res
