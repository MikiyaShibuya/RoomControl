#!/usr/bin/env python3
import requests
import argparse


def switch(base_url, bri):
    api_url = base_url + 'action'
    brightness = int(max(0, min(254, bri * 254)))
    to_on = brightness != 0
    payload = {'on': to_on, 'bri': brightness}

    res = requests.put(api_url, json=payload)


def main(hue_user, bri):

    base_url = f'http://192.168.11.3/api/{hue_user}/groups/1/'
    switch(base_url, bri)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='python hue control script')
    parser.add_argument('-u', type=str, required=True,
                        help='User name for HUE api')
    parser.add_argument('-b', type=int, required=True,
                        help='brightness (0-100)')

    args = parser.parse_args()

    hue_user = ''

    with open(args.u) as f:
        hue_user = f.read().splitlines()[0]

    main(hue_user, args.b / 100.0)


