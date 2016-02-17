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
    
    def __init__(self, ip, port, keyset):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.keyset = keyset

    def send(self, msg):
        self.sock.send(''.join(chr(msg)))

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
    
    def login(self, usePresenceChallenge=True):
        # step 1
        msg = [
            0x00,  # message identifier (MI)
            0x42   # protocol version
        ]
        self.send(msg)

        # step 2
        inp = self.recv(0x01, 17)
        tc = inp[1:16]

        # step 3
        mode = 0x01 if self.usePresenceChallenge else 0x00
        nc = self.toBytes(random.SystemRandom()) # check if this has enough entropy
        mac = self.hmac(tc + 
    
        
