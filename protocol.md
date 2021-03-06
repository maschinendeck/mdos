HMAC: always HMAC-SHA256

PC: 4 Byte. Each byte encodes one digit. 0xffffffff encodes no presence challenge
MODE: 0x00 (no presence challenge), 0x01 (use presence challenge)

1. Pi -> ESP
   TRIGGER
   
   D0: 0x00 (message identifier)
   D1: 0x42 (protocol version)

2. ESP -> Pi 
   TRIGGER CHALLENGE (TC)
   
   D0: 0x01 (message identifier)
   D1-16: TC
   
3. Pi -> ESP
   MODE + NC + HMAC(TC+MODE+NC,K0)
   
   D0: 0x02
   D1: 0x00 (w/o presence challenge)
	   0x01 (with presence challenge)
   D2-17: NC
   D18-49: HMAC
   
4. ESP -> Pi
   OPENING CHALLENCE (OC)
   
   D0: 0x03
   D1-16: OC

5. Pi -> ESP
   ACKNOWLEDGE CHALLENGE (AC) + HMAC(NC+PC+OC+AC,K1)
                                        ^ depending on mode, see above
   
   D0: 0x04
   D1-16: AC
   D17-48: HMAC
   
6. ESP -> Pi
   HMAC(AC,K2)
   
   D0: 0x05
   D1-32: HMAC
   
==== PING/PONG ====

D0: 0x23

RESPONSE: 0x42

==== ROOM STATE ====

D0: 0x10
D1: 0x01 if room is open else 0x00
   
==== dev keys ====

K0 = 0xdecafbeddeadbeefcaffeebabe421337
K1 = 0xbe421337decafbeddeadbeefcaffeeba
K2 = 0xcaffeebabe421337decafbeddeadbeef
