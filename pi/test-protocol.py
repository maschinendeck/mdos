#!/usr/bin/python

import socket
import sys

MDOS_IP = '127.0.0.1'
MDOS_PORT = 42002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((MDOS_IP, MDOS_PORT))

if len(sys.argv) > 1 and sys.argv[1] == '--close':
    s.send('close\n')
    sys.exit(0)
    

print "sent start"
s.send('start\n')
sid = s.recv(1024)
s.close()
if sid == '1':
    print "Login without presence challenge succeeded:"
elif sid == '0':
    print "Login without presence challenge failed."
else:
    print "sid is %s" % sid
    pc = int(raw_input("Enter challenge: "))
    msg = 'finish %s %04d\n' % (sid, pc)
    print "sent %s" % msg
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((MDOS_IP, MDOS_PORT))
    s.send(msg)
    res = s.recv(1)
    s.close()
    
    
    if res == '1':
        print "Login successful."
    else:
        print "Login failed!"
    
