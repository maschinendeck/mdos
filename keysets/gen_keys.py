#!/usr/bin/python

import random,json

keynames = ["K0","K1","K2"]
keys = {}

for key in keynames:
    keys[key] = []
    for i in range(0,16):
        keys[key].append("0x" + "{:02x}".format(random.randint(0,255)))
    print "static char %s[] = { %s };" % (key, ",".join(keys[key]))

#print json.dumps(keys)
