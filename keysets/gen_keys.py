#!/usr/bin/python

import random,json

keynames = ["k0","k1","k2","kh0","kh1"]
keys = {}

for key in keynames:
    keys[key] = ""
    for i in range(0,16):
        keys[key] += "{:02x}".format(random.randint(0,255))

print json.dumps(keys)
