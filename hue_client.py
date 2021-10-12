import requests
import argparse


def switch(base_url, to_on):
    api_url = base_url + 'action'
    payload = {'on': to_on}

    res = requests.put(api_url, json=payload)


def main(hue_user, inst):

    base_url = f'http://192.168.1.58/api/{hue_user}/groups/1/'

    if inst:
        # switch(base_url, False)
        switch(base_url, True)
    else:
        switch(base_url, False)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='python hue control script')
    parser.add_argument('-u', type=str, required=True,
                        help='User name for HUE api')
    parser.add_argument('-i', type=int, required=True,
                        help='ON(1) or OFF(0)')

    args = parser.parse_args()

    hue_user = ''

    with open(args.u) as f:
        hue_user = f.read().splitlines()[0]

    main(hue_user, bool(args.i))

