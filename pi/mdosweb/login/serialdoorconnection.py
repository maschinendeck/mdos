import serial
import re
import fcntl
from django.conf import settings


def sendAndExpect(message, code):
    with serial.Serial(settings.MDOS_PORT, settings.MDOS_BAUD, timeout=1) as ser:
        fcntl.flock(ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        ser.reset_input_buffer()
        ser.write(message)
        while True:
            line = ser.readline()
            print "Received:", line
            if line.startswith('0'): # debug output
                continue
            if line.startswith('505 '):
                raise Exception("Wrong presence challenge (or other frontend error).")
            if line.startswith('4') or line.startswith('5'): # error condition
                raise Exception("Error! MDOS backend says: %s" % line.strip())
            if line.startswith(str(code) + ' '):
                return True
            if len(line.strip()) == 0:
                raise Exception("Error! Frontend did not answer in time.")
            raise Exception("Error! MDOS backend responded with unexpected data: %s" % line.strip())
    
    
def startSession():
    sendAndExpect('start\n', 100)
    
def finishSession(code):
    code = str(code)

    if not re.match("^\d\d\d\d$", code):
        raise Exception("This is not a valid code. Valid codes are four digit strings.")

    sendAndExpect(code, 200)

def closeDoor():
    sendAndExpect('close\n', 200)

def setRoomState(state):
    message = 'room_state_open\n' if state else 'room_state_closed\n'
    sendAndExpect(message, 200)
