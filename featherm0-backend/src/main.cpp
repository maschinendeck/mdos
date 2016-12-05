#include <RFM69.h>    //get it here: https://www.github.com/lowpowerlab/rfm69
#include <SPI.h>

#include <Arduino.h>

#include <SHA256.h>
#include <Crypto.h>
#include <RNG.h>
//#include <TransistorNoiseSource.h>

static char K0[] = { 0xde, 0xca, 0xfb, 0xad, 0xde, 0xad, 0xbe, 0xef, 0xca, 0xff, 0xee, 0xba, 0xbe, 0x42, 0x13, 0x37};
static char K1[] = { 0xbe, 0x42, 0x13, 0x37, 0xde, 0xca, 0xfb, 0xad, 0xde, 0xad, 0xbe, 0xef, 0xca, 0xff, 0xee, 0xba };
static char K2[] = { 0xca, 0xff, 0xee, 0xba, 0xbe, 0x42, 0x13, 0x37, 0xde, 0xca, 0xfb, 0xad, 0xde, 0xad, 0xbe, 0xef };


#define FREQUENCY     RF69_433MHZ
#define ENCRYPTKEY    "1234567890123456" //exactly the same 16 characters/bytes on all nodes!
#define SERIAL_BAUD   115200
#define IS_RFM69HCW   true // set to 'true' if you are using an RFM69HCW module

#define RFM69_CS      8
#define RFM69_IRQ     3
#define RFM69_IRQN    3  // Pin 3 is IRQ 3!
#define RFM69_RST     4

#define RADIO_TIMEOUT 2000

#define FRONTEND_NODEID 23
#define BACKEND_NODEID 42
#define NETWORKID 74

#define CMD_START_WITHOUT_PRESENCE_CHALLENGE "0"
#define CMD_START_WITH_PRESENCE_CHALLENGE "1"
#define CMD_CLOSE_DOOR "8"
#define CMD_SELFTEST "9"

#define NCLEN 16
#define OCLEN 16
#define ACLEN 16
#define TCLEN 16
#define MACLEN 32

#define RELAY0 9
#define RELAY1 10
#define RELAY2 11
#define RELAY3 12


RFM69 radio = RFM69(RFM69_CS, RFM69_IRQ, IS_RFM69HCW, RFM69_IRQN);
//TransistorNoiseSource noise1(A1);
//TransistorNoiseSource noise2(A2);
SHA256 hash;


void sendMdosMessage(char*msg, int len);
bool waitForMessage(char msgid, int len);
void hmac(char* dest, char* data, int len, char* key);
void startSession(int usePresenceChallenge);
void finishSession(char* pc, char* nc, char* oc);
void selftest();
void openDoor();
void closeDoor();

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.println("000 MDOS BACKEND STARTED");

  // Hard Reset the RFM module
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, HIGH);
  delay(100);
  digitalWrite(RFM69_RST, LOW);
  delay(100);
 
  // Initialize radio
  radio.initialize(FREQUENCY,BACKEND_NODEID,NETWORKID);
  if (IS_RFM69HCW) {
    radio.setHighPower();    // Only for RFM69HCW & HW!
  }
  radio.setPowerLevel(31); // power output ranges from 0 (5dBm) to 31 (20dBm)
  
  radio.encrypt(ENCRYPTKEY);
  
  Serial.print("001 Transmitting at ");
  Serial.print(FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(" MHz");


  RNG.begin("mdos frontend", 0);
  //RNG.stir(K0, 16);
  //RNG.stir(K1, 16);
  //RNG.stir(K2, 16);  
  //RNG.addNoiseSource(noise1);
  //RNG.addNoiseSource(noise2);

  pinMode(RELAY0, OUTPUT);
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(RELAY3, OUTPUT);
  digitalWrite(RELAY0, HIGH);
  digitalWrite(RELAY1, HIGH);
  digitalWrite(RELAY2, HIGH);
  digitalWrite(RELAY3, HIGH);
}

void loop() {
  char in[3];
  if (Serial.readBytes(in, 1) < 1) {
    return;
  }
  in[1] = 0x0;
  if (strcmp(in, CMD_START_WITH_PRESENCE_CHALLENGE) == 0) {
    startSession(1);
  } else if (strcmp(in, CMD_START_WITHOUT_PRESENCE_CHALLENGE) == 0) {
    startSession(0);
  } else if (strcmp(in, CMD_SELFTEST) == 0) {
    selftest();
  } else if (strcmp(in, CMD_CLOSE_DOOR) == 0) {
    closeDoor();
    Serial.println("200 OK");
  } else {
    Serial.println("400 Unknown command.");
  }
}

bool sendMessage(char* msg, int len) {
  if (! radio.sendWithRetry(FRONTEND_NODEID, msg, len)) {
    Serial.println("556 Radio timeout while sending.");
    return 0;
  }
  return 1;
}

bool waitForMessage(char msgid, int len) {
  Serial.println("002 Waiting for response...");
  int timeout = millis() + RADIO_TIMEOUT;
  while (! radio.receiveDone()) {
    if (millis() > timeout) {
      Serial.println("555 Radio timeout.");
      return 0;
    }
  };
  if (radio.DATA[0] != msgid) {
    Serial.print("501 Error! Expected message id ");
    Serial.print(msgid);
    Serial.print(" but received message with id ");
    Serial.println(radio.DATA[0]);
    return 0;
  }
  if (radio.DATALEN != len) {
    Serial.print("502 Error! Expected message length ");
    Serial.print(radio.DATALEN);
    Serial.print(" but received message with length ");
    Serial.println(radio.DATALEN);
    return 0;
  }
  if (radio.SENDERID != FRONTEND_NODEID) {
    Serial.print("503 Error! Expected message from ");
    Serial.print(FRONTEND_NODEID);
    Serial.print(" but received message from ");
    Serial.println(radio.SENDERID);
    return 0;
  }
  if (radio.ACKRequested())
    {
      radio.sendACK();
    }
  return 1;
}

void hmac(char* dest, char* data, int len, char* key) {
  hash.resetHMAC(key, sizeof(key));
  hash.update(data, len);
  hash.finalizeHMAC(key, sizeof(key), dest, 32);
}

void startSession(int usePresenceChallenge){
  char radiopacket[RF69_MAX_DATA_LEN] = { 0x23 }; // ping
  Serial.println("010 Pinging door unit.");
  if (! sendMessage(radiopacket, 1)) return;
  if (! waitForMessage(0x42, 1)) return; // pong

  Serial.println("011 Step 1");
  radiopacket[0] = 0x00;
  radiopacket[1] = 0x42; // first message, protocol version 0x42
  if (! sendMessage(radiopacket, 2)) return;
  
  Serial.println("012 Step 2");
  if (! waitForMessage(0x01, 1+TCLEN)) return;
  char tc[TCLEN];
  int i;
  for (i=0; i<TCLEN; i++) {
    tc[i] = radio.DATA[i+1];
  }

  Serial.println("013 Step 3");
  char nc[NCLEN];
  RNG.rand((uint8_t*)nc, NCLEN);
  char data[TCLEN + 1 + NCLEN];
  memcpy(data, tc, TCLEN);
  memset(data + TCLEN, usePresenceChallenge, 1);
  memcpy(data + TCLEN + 1, nc, NCLEN);
  char mac[MACLEN];
  hmac(mac, data, sizeof(data), K0);
  memset(radiopacket, 0x02, 1);
  memset(radiopacket + 1, usePresenceChallenge, 1);
  memcpy(radiopacket + 2, nc, NCLEN);
  memcpy(radiopacket + 2 + NCLEN, mac, MACLEN);
  if (! sendMessage(radiopacket, 2+NCLEN+MACLEN)) return;

  Serial.println("014 Step 4");
  if (! waitForMessage(0x03, 1+OCLEN)) return;
  char oc[16];
  for (i=0; i<OCLEN; i++) {
    oc[i] = radio.DATA[i+1];
  }


  char pc[2] = {0xFF, 0xFF};
  if (usePresenceChallenge) {
    Serial.println("100 Waiting for Presence Challenge.");
    while (Serial.readBytes(pc, 2) < 2);
  }
  finishSession(pc, nc, oc);
}

void finishSession(char* pc, char* nc, char* oc) {
  Serial.println("015 Step 5");
  char ac[16];
  RNG.rand((uint8_t*)ac, 16);
  char data[NCLEN+2+OCLEN+ACLEN];
  memcpy(data, nc, NCLEN);
  memcpy(data+NCLEN, pc, 2);
  memcpy(data+NCLEN+2, oc, OCLEN);
  memcpy(data+NCLEN+2+OCLEN, ac, ACLEN);
  char mac[MACLEN];
  hmac(mac, data, sizeof(data), K1);
  char radiopacket[RF69_MAX_DATA_LEN] = { 0x04 };

  memcpy(radiopacket+1, ac, ACLEN);
  memcpy(radiopacket+1+ACLEN, mac, MACLEN);
  if (!sendMessage(radiopacket, 1+ACLEN+MACLEN)) return;

  Serial.println("016 Step 6");
  hmac(mac, ac, ACLEN, K2);
  if (! waitForMessage(0x05, 33)) return;
  int i;
  short isCorrect=1;
  for (i=0; i<MACLEN; i++) { // we could use memcmp, but that may lead to timing sidechannels.
    if (mac[i] != radio.DATA[1+i]) {
      isCorrect = 0;
    }
  }
  if (isCorrect == 1) {
    openDoor();
    Serial.println("200 OK");
  } else {
    Serial.println("504 Illegal mac received!");
  }
}

void openDoor() {
  Serial.println("020 Door open.");
  digitalWrite(RELAY0, LOW);
  delay(500);
  digitalWrite(RELAY0, HIGH);
  delay(3000);
}

void closeDoor() {
  Serial.println("021 Door close.");
  digitalWrite(RELAY1, LOW);
  delay(500);
  digitalWrite(RELAY1, HIGH);
  delay(3000);
}

void selftest() {
  Serial.println("090 Selftest init.");
  Serial.println("091 Relay 0.");
  digitalWrite(RELAY0, LOW);
  delay(500);
  digitalWrite(RELAY0, HIGH);
  delay(3000);

  Serial.println("091 Relay 1.");
  digitalWrite(RELAY1, LOW);
  delay(500);
  digitalWrite(RELAY1, HIGH);
  delay(3000);

  Serial.println("091 Relay 2.");
  digitalWrite(RELAY2, LOW);
  delay(500);
  digitalWrite(RELAY2, HIGH);
  delay(3000);

  Serial.println("091 Relay 3.");
  digitalWrite(RELAY3, LOW);
  delay(500);
  digitalWrite(RELAY3, HIGH);
  delay(3000);

  Serial.println("099 Selftest complete.");
}
