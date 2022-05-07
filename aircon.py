#!/usr/bin/env python3

import sys
import subprocess

def get():
    print("0")
    return 0


def set():

    key = sys.argv[3]
    value = sys.argv[4]

    if key == 'Active' and value == '1':
        subprocess.run(['python3', '/home/pi/RoomControl/irrp.py', '-p', '-g17', '-f', '/home/pi/RoomControl/codes', 'aircon:auto'])
    elif key == 'Active' and value == '0':
        subprocess.run(['python3', '/home/pi/RoomControl/irrp.py', '-p', '-g17', '-f', '/home/pi/RoomControl/codes', 'aircon:off'])
    else:
        subprocess.run(['python3', '/home/pi/RoomControl/irrp.py', '-p', '-g17', '-f', '/home/pi/RoomControl/codes', 'aircon:auto'])



if __name__ == "__main__":

    act = sys.argv[1]
    tgt = sys.argv[2]

    if act == 'Get':
        get()
    elif act == 'Set':
        set()

        

