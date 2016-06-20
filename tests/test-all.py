import lupa
from lupa import LuaRuntime
import socket
import threading
import sys
import hashlib
import hmac
from Crypto.Cipher import AES
import json

lua = LuaRuntime(unpack_returned_tuples=True, encoding=None)

lua_fun_queue = []

MAINFILE = '../esp/main.lua'

def get_file_contents(f):
    with open(f, 'r') as f:
        return f.read()

class lua_file(object):
    files = {
        'config.json': get_file_contents('../esp/config.json'),
        'keys.json': get_file_contents('../keysets/testing.json'),
    }
    last_file = None
    
    @staticmethod
    def exists(filename):
        return filename in lua_file.files

    @staticmethod
    def open(filename, mode):
        lua_file.last_file = filename
        if mode == 'w':
            lua_file.files[filename] = ''

    @staticmethod
    def write(contents):
        lua_file.files[lua_file.last_file] += contents

    @staticmethod
    def read(len):
        return lua_file.files[lua_file.last_file]
                
    @staticmethod
    def close():
        lua_file.last_file = None

class lua_cjson(object):
    @staticmethod
    def decode(s):
        print s
        return json.loads(s)

class lua_gpio(object):
    OUTPUT = None
    LOW = None
    HIGH = None
    
    @staticmethod
    def mode(a, b):
        pass

    @staticmethod
    def write(a,b):
        pass

class LuaClientSocketProxy(object):
    def __init__(self, cs, address):
        self._cs = cs
        self._address = address

    def getpeer(self):
        return self._address

    def close(self):
        print "SIM: close client socket proxy"
        self._cs.close()

    def send(self, msg):
        self._cs.send(msg)
        
    def __getattr__(self, name):
        return getattr(self._cs, name)
  
class ClientSocketWrapper():
    callbacks = {}
    
    def __init__(self, clientsocket, address):
        print "SIM: client socket wrapper started for %r" % (address,)
        self.clientsocket = clientsocket
        self.clientsocket_proxy = LuaClientSocketProxy(clientsocket, address)
        self.address = address

    def run_once(self):
        #print "SIM: client socket callbacks: %r" % (self.callbacks,)
        
        data = self.clientsocket.recv(1024)
        if data != '':
            print "SIM: Received: %r" % data
        if data != '' and 'receive' in self.callbacks:
            self.callbacks['receive'](self.clientsocket_proxy, data)
        
    def on(self, event, function):
        print 'SIM: added callback for ' + event
        self.callbacks[event] = function

    
class SocketWrapper(object):
    acceptedsockets = []
    
    def listen(self, port, established):
        serversocket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('127.0.0.1', port))
        serversocket.listen(5)
        serversocket.settimeout(0.01)
        while 1:
            try:
                x = serversocket.accept()
            except socket.timeout:
                pass
            else:
                c = ClientSocketWrapper(*x)
                established(c)
                self.acceptedsockets.append(c)
                
            for i, s in enumerate(self.acceptedsockets):
                try:
                    s.run_once()
                except socket.error:
                    print "SIM: Socket was closed."
                    del self.acceptedsockets[i]

            while len(lua_fun_queue) > 0:
                lua_fun_queue.pop(0)()
                

class lua_crypto(object):
    @staticmethod
    def encrypt(mode, key, message):
        enc = AES.new(key, AES.MODE_ECB)
        return enc.encrypt(message)

    @staticmethod
    def hmac(mode, message, key):
        out = hmac.new(key, message, digestmod=hashlib.sha256).digest()
        return out

        
            
class lua_net(object):
    TCP = None
    
    @staticmethod
    def createServer(*args):
        return SocketWrapper()


class lua_display(object):

    @staticmethod
    def off():
        print "Display: off"

    @staticmethod
    def write_open():
        print "Display: OPEN"

    @staticmethod
    def write_fail():
        print "Display: FAIL"

    @staticmethod
    def write_num_reverse(num):
        print "Display: %s" % ("%04d" % num)[-1::-1]

class lua_tmr(object):
    slots = {}
    ALARM_SINGLE = None

    @staticmethod
    def start(num):
        lua_tmr.slots[num].start()

    @staticmethod
    def unregister(num):
        if num in lua_tmr.slots:
            lua_tmr.slots[num].cancel()
            del lua_tmr.slots[num]

    @staticmethod
    def state(num):
        return None if num not in lua_tmr.slots else True
            
    @staticmethod
    def register(num, timeout, mode, handler):
        def run_timer():
            lua_fun_queue.append(handler)
        lua_tmr.slots[num] = threading.Timer(timeout/1000, run_timer)
        

def lua_print(text):
    print "LUA: %s" % text
        
lua.globals()['file'] = lua_file
lua.globals()['gpio'] = lua_gpio
lua.globals()['net'] = lua_net
lua.globals()['tmr'] = lua_tmr
lua.globals()['print'] = lua_print
lua.globals()['crypto'] = lua_crypto
lua.globals()['cjson'] = lua_cjson
for fun in ['off', 'write_open', 'write_fail', 'write_num_reverse']:
    lua.globals()['disp_%s' % fun] = getattr(lua_display, fun)

luafile = get_file_contents(MAINFILE)    
lua.execute(luafile)
