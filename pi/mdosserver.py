#!/usr/bin/python

import socket
import hashlib
import hmac
import random
import struct
import logging
import sys
import optparse
import json
import os

from gpiozero import DigitalOutputDevice
from time import sleep

logging.basicConfig(
    level=logging.DEBUG,
    format='%(relativeCreated)6d %(levelname)10s %(name)-20s %(message)s // %(filename)s:%(lineno)s',
)


ESP_ADDR = os.environ.get('ESP_ADDR', '10.172.3.3')
ESP_PORT = int(os.environ.get('ESP_PORT', '42001'))

LISTEN_ADDR = os.environ.get('LISTEN_ADDR', 'localhost')
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', '42002'))

DEFAULT_KEYSET = os.environ.get('KEYSET', "../keysets/testing.json")

GPIO_OPEN = DigitalOutputDevice(3, active_high=False, initial_value=False)
GPIO_CLOSE = DigitalOutputDevice(2, active_high=False, initial_value=False)

def openInnerDoor():
    logging.debug("Opening inner door.")
    GPIO_OPEN.blink(n=1)

def closeInnerDoor():
    logging.debug("Closing inner door.")
    GPIO_CLOSE.blink(n=1)


    
class MdosProtocolException(Exception):
    pass

class DoorConnection(object):
    BUFFER_SIZE = 64
    
    def __init__(self, ip, port, keyset_file):
        self.init_keyset(keyset_file)
        self.sessions = {}
        self.ip = ip
        self.port = port

    def init_keyset(self, keyset_file):
        with open(keyset_file, 'r') as f:
            self.keyset = {k: int(v, 16) for k,v in json.loads(f.read()).items()}
        
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
        out = hmac.new(self.toBytes(self.keyset["k%d" % keyid]), msg, digestmod=hashlib.sha256).digest()
    
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

    parser = optparse.OptionParser()
    parser.add_option("-t", "--test", dest='test', default=False, help='Test the lock without listening for commands.', action='store_true')
    parser.add_option("-s", "--simulate", dest='simulate', default=False, help='Just listen for commands without communicating to the lock.', action='store_true')
    parser.add_option("-l", "--listen-addr", dest='listenaddr', default=LISTEN_ADDR, help='Listen to this IP (default: %s).' % LISTEN_ADDR)
    parser.add_option("-p", "--listen-port", dest='listenport', default=LISTEN_PORT, help='Listen to this port (default: %d).' % LISTEN_PORT)
    parser.add_option('-d', "--door-addr", dest='dooraddr', default=ESP_ADDR, help='Communicate to the door lock on this ip (default: %s).' % ESP_ADDR)
    parser.add_option('-b', "--door-port", dest='doorport', default=ESP_PORT, help='Communicate to the door lock on this port (default: %d).' % ESP_PORT)
    parser.add_option('-k', "--keyset-file", dest="keyset", default=DEFAULT_KEYSET, help='Keyset file (default: %s).' % DEFAULT_KEYSET)
    options, args = parser.parse_args(sys.argv)

    if not options.simulate:
        door = DoorConnection(options.dooraddr, int(options.doorport), options.keyset)
        logging.info("Server started.")
    else:
        door = DummyDoorConnection()
        logging.info("Dummy server started.")
        
    if options.test:
        sid = door.startSession(True)
        pc_str = raw_input('Presence challenge: ').strip()
        pc = ''.join(DoorConnection.toBytes(int(c), 1) for c in pc_str)
        if door.finishSession(sid, pc):
            openInnerDoor()
            sleep(2)
        sys.exit("Test finished")
    
    #create an INET, STREAMing socket
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    #bind the socket to a public host,
    # and a well-known port
    serversocket.bind((options.listenaddr, options.listenport))
    #become a server socket
    serversocket.listen(5)

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
                    if res:
                        openInnerDoor()
                elif cmd[0] == 'close':
                    closeInnerDoor()    
            except MdosProtocolException, e:
                logging.exception(e)
                clientsocket.send('e')
            f.close()
            clientsocket.close()
    finally:
        serversocket.close()
        clientsocket.close()
