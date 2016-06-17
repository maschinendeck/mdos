import lupa
from lupa import LuaRuntime
import socket
import threading

lua = LuaRuntime(unpack_returned_tuples=True)

class lua_file(object):
    files = {}
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

class ClientSocketWrapper(object):
    callbacks = {}
    
    def __init__(self, clientsocket, address):
        self.clientsocket = clientsocket
        self.socketfile = clientsocket.makefile()
        self.address = address
        threading.Thread(target=self.run).run()

    def run(self):
        
        while 1:
            data = self.socketfile.read()
            if 'recv' in self.callbacks:
                self.callbacks['recv'](self.clientsocket, data)
        
    def on(self, event, function):
        self.callbacks[event] = function

    
class SocketWrapper(object):
    @staticmethod
    def listen(self, port, established):
        serversocket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('127.0.0.1', port))
        serversocket.listen(5)
        while 1:
            ClientSocketWrapper(*serversocket.accept())
                
class lua_net(object):
    TCP = None
    
    @staticmethod
    def createServer(*args):
        return SocketWrapper()

        
        
lua.globals()['file'] = lua_file
lua.globals()['gpio'] = lua_gpio
lua.globals()['net'] = lua_net

with open('../esp/main.lua') as f:
    mainfile = f.read()

luapreamble = """ """
    
lua.execute(luapreamble + mainfile)
