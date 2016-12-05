#include <RFM69.h>
#include <SPI.h>
#include "config.h"
#include "mdos.h"

#define FREQUENCY     RF69_433MHZ
#define IS_RFM69HCW    true

#define RFM69_CS      8
#define RFM69_IRQ     3
#define RFM69_IRQN    3  // Pin 3 is IRQ 3!
#define RFM69_RST     4

RFM69 radio = RFM69(RFM69_CS, RFM69_IRQ, IS_RFM69HCW, RFM69_IRQN);

void rf_setup() {
  // Hard Reset the RFM module
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, HIGH);
  delay(100);
  digitalWrite(RFM69_RST, LOW);
  delay(100);

  // Initialize radio
  radio.initialize(FREQUENCY,FRONTEND_NODEID,NETWORKID);
  if (IS_RFM69HCW) {
    radio.setHighPower();    // Only for RFM69HCW & HW!
  }
  radio.setPowerLevel(31); // power output ranges from 0 (5dBm) to 31 (20dBm)
  
  radio.encrypt(ENCRYPTKEY);
}

void rf_loop() {
  char reply_msg[50];
  
  if (radio.receiveDone())
  {
    //print message received to serial
    Serial.print('[');Serial.print(radio.SENDERID);Serial.print("] ");
    Serial.print((char*)radio.DATA);
    Serial.print("   [RX_RSSI:");Serial.print(radio.RSSI);Serial.print("]");


    mdos_recv((char *)radio.DATA, reply_msg);
    if (reply_msg[0] != 0x00) {
      if (radio.ACKRequested()) // needs to be put before something is sent!
	{
	  radio.sendACK();
	  Serial.println(" - ACK sent");
	}


      if (radio.sendWithRetry(BACKEND_NODEID, reply_msg, strlen(reply_msg))) { //target node Id, message as string or byte array, message length
	Serial.println("Sent OK");
      }

    }
  }
  
  Serial.flush();
  
  radio.receiveDone(); //put radio in RX mode
}
