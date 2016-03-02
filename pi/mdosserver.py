#!/usr/bin/python

import socket
import hashlib
import hmac
import random
import struct
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(relativeCreated)6d %(levelname)10s %(name)-20s %(message)s // %(filename)s:%(lineno)s',
)


ESP_IP = '10.172.44.91'
ESP_PORT = 42001

LISTEN_ADDR = 'localhost'
LISTEN_PORT = 42002

KEYSET = {
    0: 0xdecafbeddeadbeefcaffeebabe421337,
    1: 0xbe421337decafbeddeadbeefcaffeeba,
    2: 0xcaffeebabe421337decafbeddeadbeef,
}

class MdosProtocolException(Exception):
    pass

class DoorConnection(object):
    BUFFER_SIZE = 64
    
    def __init__(self, ip, port, keyset):
        self.keyset = keyset
        self.sessions = {}

    def connect(self):
        logging.debug("door connection started. ip=%s:%d" % (ip, port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.getUserChallengeCB = getUserChallengeCB

    def disconnect(self):
        self.socket.close()

    def send(self, msg):
        l = len(msg)
        logging.debug("Send message: %r" % msg)
        sent = self.socket.send(msg) # ''.join(chr(msg)))
        if sent < l:
            logging.debug("Only %d of %d bytes sent. Retrying." % (sent, l))
            
            #self.send(msg[sent:])

    def recv(self, checkMessageIdentifier=None, checkMessageLength=None):
        logging.debug("Waiting for message.")
        inp = self.socket.recv(self.BUFFER_SIZE)
        if len(inp) == 0:
            raise MdosProtocolException("Received empty response.")
        logging.debug("Received message: %r" % inp)
        if checkMessageIdentifier is not None and inp[0] != chr(checkMessageIdentifier):
            raise MdosProtocolException(
                "Expected message identifier %x, received %r!" % (checkMessageIdentifier, inp[0]))
        if checkMessageLength is not None and len(inp) != checkMessageLength:
            raise MdosProtocolException(
                "Expected message length %s, received %s!" % (checkMessageLength, len(inp)))
        return inp

    def hmac(self, msg, keyid):
        return hmac.new(self.keyset[keyid], msg, digestmod=hashlib.sha256).digest()

    @staticmethod
    def toBytes(num, bytes=16):
        s = '%x' % num
        if len(s) & 1:
            s = '0' + s
        res = s.decode('hex')
        return "\0" * (bytes - res) + res
    
    def getNonce(self):
        return self.toBytes(random.SystemRandom().getrandbits(16 * 8))

    def startSession(self, usePresenceChallenge):
        self.connect()
        
        # step 0
        msg = "\x23"
        self.send(msg)
        self.recv(0x42, 1)
        logging.info("Successfully pinged door unit.")
        
        # step 1
        msg = "\x00\x42"  # message identifier and protocol version
        
        self.send(msg)

        # step 2
        logging.debug("Step 2")
        inp = self.recv(0x01, 17)
        tc = inp[1:16]

        # step 3
        logging.debug("Step 3")
        mode = 0x01 if usePresenceChallenge else 0x00
        nc = self.getNonce() # check if this has enough entropy
        mac = self.hmac(tc + mode + nc, 0)
        msg = chr(0x02) + chr(mode) + nc + hmac
        self.send(msg)
    
        # step 4
        logging.debug("Step 4")
        inp = self.recv(0x03, 17)
        oc = inp[1:16]

        self.disconnect()

        sid = random.SystemRandom().getrandbits(16 * 8)
        self.sessions[sid] = [nc, oc]

        if usePresenceChallenge:
            return sid
        else:
            return self.finishSession(sid, "\xff\xff")

    def finishSession(self, sid, userChallenge):
        self.connect()
        pc = userChallenge # for user input, use toBytes(self.getUserChallengeCB(), 2)

        nc, oc = self.sessions[sid]
        del self.sessions[sid]
        
        # step 5
        logging.debug("Step 5")
        ac = self.getNonce()
        mac = self.hmac(nc + pc + oc + ac, 1)

        self.send("\x04" + ac + mac)

        # step 6
        logging.debug("Step 6")
        inp = self.recv(0x05, 33)
        mac = inp[1:32]
        expmac = self.hmac(ac, 2)

        self.disconnect()

        if mac != expmac:
            raise MdosProtocolException("In message 0x05: illegal hmac. Expected %s..., received %s..." % (expmac[:8], mac[:8]))
        return True

if __name__ == "__main__":
    #create an INET, STREAMing socket
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    #bind the socket to a public host,
    # and a well-known port
    serversocket.bind((LISTEN_ADDR, LISTEN_PORT))
    #become a server socket
    serversocket.listen(5)

    door = DoorConnection(ESP_IP, ESP_PORT, KEYSET)

    logging.info("Server started.")
    
    while 1:
        #accept connections from outside
        (clientsocket, address) = serversocket.accept()
        f = clientsocket.makefile()
        cmd = f.readline().strip().split(' ')
        logging.info("Received: '%s'" % cmd)
        if cmd[0] == 'start':
            clientsocket.send(door.startSession(True))
        elif cmd[0] == 'finish':
            sid = int(cmd[1])
            pc = DoorConnection.toBytes(int(cmd[2]))
            res = door.finishSession(sid, pc)
            clientsocket.send('1' if res else '0')
        f.close()
        clientsocket.close()
