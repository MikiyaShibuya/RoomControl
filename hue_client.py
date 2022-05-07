#!/usr/bin/env python3
import requests
import argparse
import sys
import json


def on_off(base_url, to_on):
    api_url = base_url + 'action'
    payload = {'on': to_on}

    print(api_url, payload)

    res = requests.put(api_url, json=payload)


def set_brightness(base_url, bri):
    api_url = base_url + 'action'
    brightness = int(max(0, min(254, bri * 254)))
    to_on = brightness != 0
    payload = {'on': to_on, 'bri': brightness}

    print(api_url, payload)

    res = requests.put(api_url, json=payload)
    print(res)


def get(base_url):
    payload = {}
    res = requests.get(base_url, json=payload)
    data = json.loads(res.text)

    key = sys.argv[4]
    if key == "On": 
        print(data['action']['on'])
    elif key == "Brightness":
        bri = int(data['action']['bri'])
        print(int(bri / 254.0 * 100))

    return 0


def set(base_url):

    key = sys.argv[4]
    value = sys.argv[5]

    if key == "On" and value == "0":
        on_off(base_url, False)
    elif key == "On" and value == "1":
        on_off(base_url, True)
    elif key == "Brightness":
        set_brightness(base_url, int(value) / 100.0)
    else:
        print(f"unknown key: {key} - {value}")


if __name__ == "__main__":

    with open(sys.argv[1]) as f:
        hue_user = f.read().splitlines()[0]
    base_url = f'http://192.168.11.3/api/{hue_user}/groups/1/'

    act = sys.argv[2]
    tgt = sys.argv[3]

    if act == 'Get':
        get(base_url)
    elif act == 'Set':
        set(base_url)

