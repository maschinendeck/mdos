#!/usr/bin/python

import socket

MDOS_IP = '127.0.0.1'
MDOS_PORT = 42002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((MDOS_IP, MDOS_PORT))

print "sent start"
s.send('start\n')
sid = s.recv(1024)
s.close()
print "sid is %s" % sid
pc = int(raw_input("Enter challenge: "))
msg = 'finish %s %04d\n' % (sid, pc)
print "sent %s" % msg

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((MDOS_IP, MDOS_PORT))
s.send(msg)
res = s.recv(1)
s.close()


if res:
    print "Login successful."
    
