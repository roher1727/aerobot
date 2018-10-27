#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Implementation of the primary structure intended to deliver
a decision based on the current state and the user's input.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json
import traceback
import requests

from pprint import pprint

# Base URL to get user info: needs to be formatted with
# a sender_id and the page access token.
INFO_URL = 'https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic&access_token={}'

def get_user_info(sender_id):
    """Retrieves a user's main info.
    """
    url = INFO_URL.format(sender_id, os.environ['PAGE_ACCESS_TOKEN'])
    info = requests.get(url)
    if info:
        info = info.json()
        if 'error' in info.keys():
            return None
        else:
            return info
    else:
        return None


def send_message(recipient_id, message_text, quick_replies=None):
    """
    Message sending function wrapper
    """
    print('sending message to {recipient}: {text}'.format(recipient=recipient_id, text=message_text))

    params = {
        'access_token': os.environ['PAGE_ACCESS_TOKEN']
    }
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'messaging_type': 'RESPONSE',
        'recipient': {
            'id': recipient_id
        },
        'message':
        {
            'text': message_text
        }
    }
    if quick_replies:
        data['message']['quick_replies'] = quick_replies
    data = json.dumps(data)
    req = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(os.environ['PAGE_ACCESS_TOKEN']),
                        params=params,
                        headers=headers,
                        data=data)
    if req.status_code != 200:
        print(req.status_code)
        print(req.text)



class ResponseDispatcher:
    """
    A class intended to decide how to process the user's input.
    """

    def __init__(self):
        """Initializer
        """
        pass

    def dispatch(self, data):
        """Retrieves the relevant data from an incoming message, encoded in a dict.
        Interprets its content according to the type of input (file, text) found.
        """
        sender_id = None
        global_ctx = {}
        if 'entry' not in data.keys():
            self.dispatch('ERROR')
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if 'sender' in messaging_event.keys():
                    if 'id' in messaging_event['sender']:
                        # get sender ID
                        sender_id = messaging_event['sender']['id']
                        global_ctx = {'user_id': sender_id}
                        user_info = get_user_info(sender_id)
                        if user_info:
                            global_ctx.update(user_info)
                if 'postback' in messaging_event.keys():
                    if 'payload' in messaging_event['postback'].keys():
                        if messaging_event['postback']['payload'] == 'GET_STARTED_PAYLOAD':
                            # Get_Started button was pressed
                            return {'TYPE': 'START', 'CONTEXT': global_ctx}
                        else:
                            qr_payload = messaging_event['postback']['payload']
                            return {'TYPE': 'QUICK_REPLY', 'CONTEXT': global_ctx}
                if 'message' in messaging_event.keys():
                    # message has a quick reply payload
                    if 'quick_reply' in messaging_event['message'].keys():
                        if 'payload' in messaging_event['message']['quick_reply'].keys():
                            qr_payload = messaging_event['message']['quick_reply']['payload']
                            return {'TYPE': 'QUICK_REPLY', 'CONTEXT': global_ctx, 'MESSAGE': qr_payload}
                        else:
                            print('[WARNING] strange format in quick reply!')
                    # message contains text and/or attachments
                    elif 'text' in messaging_event['message'].keys():
                        # message has text
                        message = messaging_event['message']['text']
                        return {'TYPE': 'TEXT', 'CONTEXT': global_ctx, 'MESSAGE': message}
                    if 'attachments' in messaging_event['message'].keys():
                        try:
                            # grab all attachments and process them
                            attachments = []
                            for att in messaging_event['message']['attachments']:
                                if 'payload' in att.keys():
                                    if 'url' in att['payload'].keys():
                                        attachments.append(att['payload']['url'])
                            if attachments:
                                return {'TYPE': 'MEDIA', 'CONTEXT': global_ctx, 'MESSAGE': attachments}
                        except:
                            print('[WARNING] Attachment not recognized!!')
