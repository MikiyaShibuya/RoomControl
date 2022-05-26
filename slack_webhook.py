#!/usr/bin/env python3

import sys
import requests

class SlackWebhook:
  def __init__(self, config_fn):
    self.uri = ''
    self.sender_name = ''
    with open(config_fn) as f:
      self.uri = f.readline().replace('\n', '')
      self.sender_name = f.readline().replace('\n', '')

  def send_message(self, msg):
    payload = f'{{"text": "{self.sender_name} : {msg}"}}'
    return requests.post(self.uri, data=payload)

if __name__ == '__main__':
  config = sys.argv[1]
  msg = sys.argv[2]

  slack_webhook = SlackWebhook(config)
  res = slack_webhook.send_message(msg)

