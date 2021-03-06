#include "keys.h"

#define DEBUG false

#define SERIAL_BAUD 115200

#define DISP_ADDR 0x70

#define RELAY_TIMEOUT 3000
#define PROTOCOL_TIMEOUT 16000

#define NETWORKID 74
#define FRONTEND_NODEID 23
#define BACKEND_NODEID 42

#define ENCRYPTKEY     "1234567890123456" //exactly the same 16 characters/bytes on all nodes!

// static char K0[] = { 0xde, 0xca, 0xfb, 0xad, 0xde, 0xad, 0xbe, 0xef, 0xca, 0xff, 0xee, 0xba, 0xbe, 0x42, 0x13, 0x37};
// static char K1[] = { 0xbe, 0x42, 0x13, 0x37, 0xde, 0xca, 0xfb, 0xad, 0xde, 0xad, 0xbe, 0xef, 0xca, 0xff, 0xee, 0xba };
// static char K2[] = { 0xca, 0xff, 0xee, 0xba, 0xbe, 0x42, 0x13, 0x37, 0xde, 0xca, 0xfb, 0xad, 0xde, 0xad, 0xbe, 0xef };
