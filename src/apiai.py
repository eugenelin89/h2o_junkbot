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
    res = requests.post(os.environ['APIAI_QUERY_URL'], params = params, json=data, headers=headers).json()
    return res


def set_context(sender_id, context, lifespan=3):
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : os.environ['APIAI_AUTH'],
        "Accept" : "application/json"
    }
    data = [
        {
            "name" : context,
            "lifespan" : lifespan
        }
    ]
    params = {'sessionId':sender_id}
    res = requests.post(os.environ['APIAI_CONTEXT_URL'], params = params, json=data, headers=headers)
    print 'set_context result: '+ res.text
    return
