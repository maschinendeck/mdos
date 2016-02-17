import socket
import hashlib
import hmac
import random
import struct

ESP_IP = '127.0.0.1'
ESP_PORT = '42001'
KEYSET = {
    0: 0xdecafbeddeadbeefcaffeebabe421337,
    1: 0xbe421337decafbeddeadbeefcaffeeba,
    2: 0xcaffeebabe421337decafbeddeadbeef,
}

class MdosProtocolException(Exception):
    pass

class DoorConnection(object):
    BUFFER_SIZE = 64
    
    def __init__(self, ip, port, keyset, getUserChallengeCB):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.keyset = keyset
        self.getUserChallengeCB = getUserChallengeCB

    def send(self, msg):
        self.sock.send(msg) # ''.join(chr(msg)))

    def recv(self, checkMessageIdentifier=None, checkMessageLength=None):
        inp = self.sock.recv(self.BUFFER_SIZE)
        if checkMessageIdentifier is not None and inp[0] != checkMessageIdentifier:
            raise MdosProtocolException(
                "Expected message identifier %x, received %x!" % (checkMessageIdentifier, inp[0]))
        if checkMessageLength is not None and len(inp) != checkMessageLength:
            raise MdosProtocolException(
                "Expected message length %s, received %s!" % (checkMessageLength, len(inp)))
        return inp

    def hmac(self, msg, keyid):
        return hmac.new(self.keyset[keyid], msg, digestmod=hashlib.sha256).digest()

    def toBytes(self, num, bytes=16):
        s = '%x' % n
        if len(s) & 1:
            s = '0' + s
        res = s.decode('hex')
        return "\0" * (bytes - res) + res
    
    def getNonce(self):
        return self.toBytes(random.SystemRandom())

    def login(self, usePresenceChallenge=True):
        # step 1
        msg = ""
            "\x00"  # message identifier (MI)
            "\x42"  # protocol version
        
        self.send(msg)

        # step 2
        inp = self.recv(0x01, 17)
        tc = inp[1:16]

        # step 3
        mode = 0x01 if self.usePresenceChallenge else 0x00
        nc = self.getNonce() # check if this has enough entropy
        mac = self.hmac(tc + mode + nc, 0)
        msg = chr(0x02) + chr(mode) + nc + hmac
        self.send(msg)
    
        # step 4
        inp = self.recv(0x03, 17)
        oc = inp[1:16]

        if usePresenceChallenge:
            pc = toBytes(self.getUserChallengeCB(), 2)
        else:
            pc = "\xff\xff"

        # step 5
        ac = self.getNonce()
        mac = self.hmac(nc + pc + oc + ac, 1)

        self.send("\x04" + ac + mac)

        # step 6
        inp = self.recv(0x05, 33)
        mac = inp[1:32]
        expmac = self.hmac(ac, 2)
        if mac != expmac:
            raise MdosProtocolException("In message 0x05: illegal hmac. Expected %s..., received %s..." % (expmac[:8], mac[:8]))

        return True

if __name__ == "__main__":
    def dummyPCInput():
        return int(raw_input("Enter User Challenge: "))

    door = DoorConnection(ESP_IP, ESP_PORT, dummyPCInput)
    if door.login():
        print "Login successful."
        