#!/usr/bin/python

import socket

MDOS_IP = '127.0.0.1'
MDOS_PORT = 42002

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((MDOS_IP, MDOS_PORT))

socket.send('start\n')
sid = socket.recv(1024)
pc = int(raw_input("Enter challenge: "))
socket.send('finish %s %d' % (sid, pc))
res = socket.recv(1)
socket.close()


if res:
    print "Login successful."
    
