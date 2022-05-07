#!/usr/bin/env python3

import sys

print(sys.argv)

with open("/home/pi/RoomControl/test.txt", mode='a') as f:
    f.write(str(sys.argv))
    f.write('\n')
