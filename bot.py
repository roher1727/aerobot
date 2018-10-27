#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Main chatbot script.
A server is implemented to dispatch user requests.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from pprint import pprint
from flask import Flask, request
from dispatcher import ResponseDispatcher, send_message

app = Flask(__name__)
DISPATCHER = ResponseDispatcher()

@app.route('/', methods=['GET'])
def verify():
    """
    when the endpoint is registered as a webhook, it must echo back
    the 'hub.challenge' value it receives in the query arguments
    """
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == os.environ['VERIFY_TOKEN']:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200

    print('Hello world')
    return 'Hello world', 200

@app.route('/', methods=['POST'])
def webhook():
    """
    Endpoint for processing incoming messaging events
    """
    global DISPATCHER
    data = request.get_json()
    pprint(data)
    parsed = DISPATCHER.dispatch(data)
    pprint(parsed)
    send_message(parsed['CONTEXT']['user_id'], '¡Quiubo!')
    return 'ok', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)
