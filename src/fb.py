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
