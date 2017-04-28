import os, requests

def send_message(sender_id, message, quick_reply = None):
    post_msg_url = 'https://graph.facebook.com/v2.6/me/messages?access_token='+os.environ['FB_ACCESS_TOKEN']
    resp_data = {
        "recipient":{"id":sender_id},
        "message":{"text":message}
    }
    if quick_reply != None:
        resp_data["message"]["quick_replies"] = quick_reply
    res = requests.post(post_msg_url, json=resp_data)
    return res

def get_fb_profile(sender_id):
    url = os.environ['FB_GRAPHAPI_URL']+sender_id
    params = {'fields':'first_name,last_name,profile_pic,locale,timezone,gender',
    'access_token':os.environ['FB_ACCESS_TOKEN']}
    # For local testing:
    #url = 'https://graph.facebook.com/v2.6/'+sender_id
    #params = {'fields':'first_name,last_name,profile_pic,locale,timezone,gender',
    #'access_token':'EAAaZCTAZBYPfoBAF0ZC9ZBfZCCfzEHfBeOZAxU9u0PvQIWt6D3JxfBE4PaKEVelakJ8A45LkhTn802mhSiD3YvvjZAEdw2584QOZCLXhns9rqFTVZCc2SYgqcXK7JwjR394J2dZCrt6xhMfVsZBPpIIDCr5x8laKHElTUsgYj3luZBpJMwZDZD'}

    res = requests.get(url, params).json()
    return res
