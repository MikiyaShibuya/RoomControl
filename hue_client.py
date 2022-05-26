#!/usr/bin/env python3
import requests
import argparse
import sys
import json

class HueClient:
  def __init__(self, fn):
    with open(fn) as f:
      config = f.read().splitlines()
      hue_user = config[0]
      hue_url = config[1]
    self.base_url = f'http://{hue_url}/api/{hue_user}/groups/1/'
    self.table = [int(i / 100.0 * 254)for i in range(101)]

  def set_on(self, on):
    api_url = self.base_url + 'action'
    payload = {'on': on}
    res = requests.put(api_url, json=payload)

  # Set birhgtness within 0 to 100 float value
  def set_brightness(self, bri):
    api_url = self.base_url + 'action'
    bri = max(0, min(100, bri))
    bri_in_hue = self.table[bri]
    to_on = bri_in_hue != 0
    payload = {'on': to_on, 'bri': bri_in_hue}

    res = requests.put(api_url, json=payload)

  def get_on(self):
    payload = {}
    res = requests.get(self.base_url, json=payload)
    data = json.loads(res.text)
    return data['action']['on']


  # Get current brightness as [0 - 100]
  def get_brightness(self):
    payload = {}
    res = requests.get(self.base_url, json=payload)
    data = json.loads(res.text)

    bri_in_hue = int(data['action']['bri'])
    bri = self.table.index(bri_in_hue)
    return bri


def main():
  config = sys.argv[1]

  # "Get" or "Set"
  act = sys.argv[2]
  # Target name
  tgt = sys.argv[3]
  # Key of value to be get/set
  key = sys.argv[4]

  hue_client = HueClient(config)

  if act == 'Get':
    if key == 'On':
      is_on = hue_client.get_on()
      print(is_on)
      return 0
    elif key == 'Brightness':
      bri = hue_client.get_brightness()
      print(bri)
      return 0
  elif act == 'Set':
    if key == 'On':
      value = sys.argv[5]
      hue_client.set_on(value == '1')
      return 0
    elif key == 'Brightness':
      value = int(sys.argv[5])
      hue_client.set_brightness(value)
      return 0


if __name__ == "__main__":
  main()

