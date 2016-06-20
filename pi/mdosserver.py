#!/usr/bin/python

import socket
import hashlib
import hmac
import random
import struct
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(relativeCreated)6d %(levelname)10s %(name)-20s %(message)s // %(filename)s:%(lineno)s',
)


#ESP_IP = '10.172.191.159'
ESP_IP = '127.0.0.1'
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
        self.ip = ip
        self.port = port

    def connect(self):
        logging.debug("door connection started. ip=%s:%d" % (self.ip, self.port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        self.socket.settimeout(3)

    def disconnect(self):
        self.socket.close()

    # get string of bytes, return string with space-separated hex-printed bytes
    def printBytes(self, msg):
        return ' '.join("%02x" % ord(c) for c in msg)

    def send(self, msg):
        l = len(msg)
        logging.debug("Send message: %s" % self.printBytes(msg))
        self.socket.sendall(msg)

    def recv(self, checkMessageIdentifier=None, checkMessageLength=None):
        logging.debug("Waiting for message.")
        inp = self.socket.recv(self.BUFFER_SIZE)
        if len(inp) == 0:
            raise MdosProtocolException("Received empty response.")
        logging.debug("Received message: %s" % self.printBytes(inp))
        if checkMessageIdentifier is not None and inp[0] != chr(checkMessageIdentifier):
            raise MdosProtocolException(
                "Expected message identifier %x, received %r!" % (checkMessageIdentifier, inp[0]))
        if checkMessageLength is not None and len(inp) != checkMessageLength:
            raise MdosProtocolException(
                "Expected message length %s, received %s!" % (checkMessageLength, len(inp)))
        return inp

    def hmac(self, msg, keyid):
        out = hmac.new(self.toBytes(self.keyset[keyid]), msg, digestmod=hashlib.sha256).digest()
    
        logging.debug("Macing: %s -> %s" % (self.printBytes(msg), self.printBytes(out)))
        return out

    @staticmethod
    def toBytes(num, bytes=16):
        s = '%x' % num
        if len(s) & 1:
            s = '0' + s
        res = s.decode('hex')
        return "\0" * (bytes - len(res)) + res
    
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
        tc = inp[1:17]
        logging.debug("tc=%s" % self.printBytes(tc))

        # step 3
        logging.debug("Step 3")
        mode = 0x01 if usePresenceChallenge else 0x00
        nc = self.getNonce() # check if this has enough entropy
        logging.debug("nc=%s" % self.printBytes(nc))
        mac = self.hmac(tc + chr(mode) + nc, 0)
        logging.debug("mac=%s" % self.printBytes(mac))
        msg = chr(0x02) + chr(mode) + nc + mac
        self.send(msg)
    
        # step 4
        logging.debug("Step 4")
        inp = self.recv(0x03, 17)
        oc = inp[1:17]
        logging.debug("oc=%s" % self.printBytes(oc))

        sid = random.SystemRandom().getrandbits(16 * 8)
        self.sessions[sid] = [nc, oc]
        logging.debug("Session ID: %d" % sid)
        if usePresenceChallenge:
            logging.debug("Waiting for PC.")
            return sid
        else:
            logging.debug("Finishing session with FFFF:")
            return self.finishSession(sid, "\xff\xff\xff\xff")

    def finishSession(self, sid, userChallenge):
        pc = userChallenge # for user input, use toBytes(self.getUserChallengeCB(), 2)
        logging.debug("pc=%s" % self.printBytes(pc))

        nc, oc = self.sessions[sid]
        del self.sessions[sid]
        
        # step 5
        logging.debug("Step 5")
        ac = self.getNonce()
        logging.debug("ac=%s" % self.printBytes(ac))

        mac = self.hmac(nc + pc + oc + ac, 1)
        logging.debug("mac=%s" % self.printBytes(mac))

        self.send("\x04" + ac + mac)

        # step 6
        logging.debug("Step 6")
        inp = self.recv(0x05, 33)
        mac = inp[1:33]
        expmac = self.hmac(ac, 2)

        self.disconnect()

        if mac != expmac:
            raise MdosProtocolException("In message 0x05: illegal hmac. Expected %s..., received %s..." % (expmac[:8], mac[:8]))
        return True

class DummyDoorConnection(DoorConnection):

    def __init__(self, *args):
        pass

    def startSession(self, *args):
        return 42

    def finishSession(self, *args):
        return True

    
if __name__ == "__main__":

    if '--test' in sys.argv:
        door = DoorConnection(ESP_IP, ESP_PORT, KEYSET)
        sid = door.startSession(True)
        pc_str = raw_input('Presence challenge: ').strip()
        pc = ''.join(DoorConnection.toBytes(int(c), 1) for c in pc_str)
        door.finishSession(sid, pc)
        sys.exit("Test finished")
    
    #create an INET, STREAMing socket
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    #bind the socket to a public host,
    # and a well-known port
    serversocket.bind((LISTEN_ADDR, LISTEN_PORT))
    #become a server socket
    serversocket.listen(5)

    if not '--dummy' in sys.argv:
        door = DoorConnection(ESP_IP, ESP_PORT, KEYSET)
        logging.info("Server started.")
    else:
        door = DummyDoorConnection()
        logging.info("Dummy server started.")
        
    try:
        while 1:
            #accept connections from outside
            (clientsocket, address) = serversocket.accept()
            f = clientsocket.makefile()
            cmd = f.readline().strip().split(' ')
            logging.info("Received: %r" % cmd)
            try:
                if cmd[0] == 'start':
                    clientsocket.send("%d" % door.startSession(True))
                elif cmd[0] == 'finish':
                    sid = int(cmd[1])
                    pc = ''.join(DoorConnection.toBytes(int(c), 1) for c in cmd[2])
                    res = door.finishSession(sid, pc)
                    clientsocket.send('1' if res else '0')
            except MdosProtocolException, e:
                logging.exception(e)
                clientsocket.send('e')
            f.close()
            clientsocket.close()
    finally:
        serversocket.close()
        clientsocket.close()
