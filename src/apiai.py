# Example:
# curl -H "Content-Type: application/json; charset=utf-8" -H "Authorization:Bearer abcdefghijklmnopqrstuvwxyz" --data "{'query':'How are you?','lang':'en','sessionId':'1234567890'}" "https://api.api.ai/v1/query?v=20150910"

import os, requests

def query(sender_id, content):
    headers = {
        "Content-Type":"application/json; charset=utf-8",
        "Authorization":os.environ['APIAI_AUTH']
    }
    data = {
        "query":content,
        "lang":"en",
        "sessionId":sender_id
    }
    params = {'v':os.environ['APIAI_VERSION']}
    res = requests.post(os.environ['APIAI_URL'], params = params, json=data, headers=headers).json()
    return res
