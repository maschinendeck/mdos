#include <Crypto.h>
#include <SHA256.h>
#include <SimpleTimer.h>
#include <RNG.h>
#include "TransistorNoiseSource.h"
#include "display.h"
#include "config.h"

//#define LED           13  // onboard blinky

#define PIN_DEBUG_LED1 6
#define PIN_DEBUG_LED2 10
#define PIN_RAUMSTATUS_LED 11
#define PIN_RELAY 12

#define LEN_NONCE 16
#define LEN_HASH 32
#define LEN_PC 4

SimpleTimer timer;
SHA256 hash;

uint8_t state;
uint8_t tc[LEN_NONCE];
uint8_t nc[LEN_NONCE];
uint8_t oc[LEN_NONCE];
uint8_t pc[LEN_PC];

int relay_timer_id;
int protocol_timer_id;

bool relay_timer_running = false;

TransistorNoiseSource noise(A1);


void debug_led1(bool state) {
  if (state) {
    digitalWrite(PIN_DEBUG_LED1, HIGH);
  } else {
    digitalWrite(PIN_DEBUG_LED1, LOW);
  }
}

void debug_led2(bool state) {
  if (state) {
    digitalWrite(PIN_DEBUG_LED2, HIGH);
  } else {
    digitalWrite(PIN_DEBUG_LED2, LOW);
  }
}

void switch_relay(bool state) {
  if (state) {
    if(DEBUG) {
      Serial.println("relay on");
    }
    digitalWrite(PIN_RELAY, HIGH);
  } else {
    if(DEBUG) {
      Serial.println("relay off");
    }
    digitalWrite(PIN_RELAY, LOW);
  }
}

void reset() {
if (timer.isEnabled(protocol_timer_id)) {
  timer.deleteTimer(protocol_timer_id);
}

 state = 0;
 tc[0] = 0; // is this a good idea? -> I need some NULL replacement here
 nc[0] = 0;
 oc[0] = 0;
 pc[0] = 0;

 switch_relay(false);

 debug_led1(false);
 debug_led2(false);
}

void protocol_tmr_handler() {
  if(DEBUG) {
    Serial.print("protocol_tmr_handler");
    Serial.println();
    Serial.flush();
  }
  reset();
  disp_off();
}

void start_protocol_tmr() {
  protocol_timer_id = timer.setTimeout(PROTOCOL_TIMEOUT, protocol_tmr_handler);
  // enable? -> check source code
  if(DEBUG) {
    Serial.print("start_protocol_tmr ");
    Serial.print(protocol_timer_id);
    Serial.println();
    Serial.flush();
  }
}

void reset_relay_tmr() {
  if(relay_timer_running) {
    timer.deleteTimer(relay_timer_id);
  }
}

void relay_tmr_handler() {
  relay_timer_running = false;
  if(DEBUG) {
    Serial.print("relay_tmr_handler");
    Serial.println();
    Serial.flush();
  }
  switch_relay(false);
  debug_led1(false);
  debug_led2(false);
  protocol_tmr_handler();
}

void start_relay_tmr() {
  relay_timer_running = true;
  relay_timer_id = timer.setTimeout(RELAY_TIMEOUT, relay_tmr_handler);
  if(DEBUG) {
    Serial.print("start_relay_tmr ");
    Serial.print(relay_timer_id);
    Serial.println();
    Serial.flush();
  }
}

void open_door() {
  debug_led1(true);
  debug_led2(false);
  switch_relay(true);
  disp_write_open();
  start_relay_tmr();
}


void generate_nonce(uint8_t* dest) {
  RNG.rand((uint8_t *) dest, LEN_NONCE);
}

void serial_print_array(uint8_t* a, uint8_t len) {
  for (int i = 0; i < len; i++) {
    Serial.print(a[i], HEX);
    Serial.print(",");
  }
  Serial.println();
}


void process_pl_0(uint8_t *pl, uint8_t *msg, uint8_t *reply_msg_len) {
  debug_led1(true);
  debug_led2(true);
  
  if(DEBUG) {
    Serial.print("0: ");
  }
  if (relay_timer_running) {
    timer.deleteTimer(relay_timer_id);
  }
  
  *reply_msg_len = 0;

  generate_nonce(tc);

  if(DEBUG) {
    Serial.print("tc=");
    serial_print_array(tc, LEN_NONCE);
  }

  msg[0] = 0x01;
  memcpy(msg+1, tc, LEN_NONCE);
  //msg[1+LEN_NONCE] = 0x0;
  *reply_msg_len = 1+LEN_NONCE;


  state++;
}

void process_pl_2(uint8_t *pl, uint8_t *msg, uint8_t *reply_msg_len) {
  if(DEBUG) {
    Serial.print("2: ");
  }
  *reply_msg_len = 0;

  uint8_t mode = pl[1];
  memcpy(nc, pl+2, LEN_NONCE);
  uint8_t h_rec[LEN_HASH];
  memcpy(h_rec, pl+18, LEN_HASH);
  uint8_t h_own[LEN_HASH];
  hash.resetHMAC(K0, sizeof(K0));
  hash.update(tc, LEN_NONCE);
  hash.update(&mode, sizeof(mode));
  hash.update(nc, LEN_NONCE);
  hash.finalizeHMAC(K0, sizeof(K0), h_own, LEN_HASH);

  // add some debug output here
  if(DEBUG) {
    Serial.print("nc=");
    serial_print_array(nc, LEN_NONCE);
    Serial.print("my hmac=");
    serial_print_array(h_own, LEN_HASH);
    Serial.print("received hmac=");
    serial_print_array(h_rec, LEN_HASH);
    Serial.flush();
  }

  if (!memcmp(h_own, h_rec, LEN_HASH)) {
    reset_relay_tmr(); // reset timer

    generate_nonce(oc);

    if(DEBUG) {
      Serial.print("oc=");
      serial_print_array(oc, LEN_NONCE);
    }
    
    msg[0] = 0x03;

    if (mode == 0x01) {
      // generate presence challenge
      uint8_t pc_src[LEN_NONCE];
      generate_nonce(pc_src);
      long pc_num = (pc_src[0]*256 + pc_src[1]) % 10000;
      if (DEBUG) {
	Serial.print("pc=");
	Serial.print(pc_num);
	Serial.println();
      }
      disp_write_num_reverse(pc_num);
      for (int i = 0; i<4; i++) {
	pc[i] = pc_num % 10;
	pc_num = pc_num / 10;
      }
    } else {
      // CURRENTLY DISABLED
      // no presence challenge
      memset(pc, 0xff, LEN_PC);
      msg[0] = 0xff; // invalidate msg
    }

    memcpy(msg+1, oc, LEN_NONCE);
    //msg[1+LEN_NONCE] = 0x0;
    *reply_msg_len = 1 + LEN_NONCE;

    
    state++;
  } else {
    msg[0] = 0xff;
  }
}

void process_pl_4(uint8_t *pl, uint8_t *msg, uint8_t *reply_msg_len) {
  if(DEBUG) {
    Serial.print("4: ");
  }
  *reply_msg_len = 0;

  uint8_t ac[LEN_NONCE];
  memcpy(ac, pl+1, LEN_NONCE);

  uint8_t h_rec[LEN_HASH];
  memcpy(h_rec, pl+17, LEN_HASH);
  uint8_t h_own[LEN_HASH];
  hash.resetHMAC(K1, sizeof(K1));
  hash.update(nc, LEN_NONCE);
  hash.update(pc, LEN_PC);
  hash.update(oc, LEN_NONCE);
  hash.update(ac, LEN_NONCE);
  hash.finalizeHMAC(K1, sizeof(K1), h_own, LEN_HASH);

  if(DEBUG) {
    Serial.print("ac=");
    serial_print_array(ac, LEN_NONCE);
    Serial.print("my hmac=");
    serial_print_array(h_own, LEN_HASH);
    Serial.print("received hmac=");
    serial_print_array(h_rec, LEN_HASH);
    Serial.flush();
  }

  
  if (!memcmp(h_own, h_rec, LEN_HASH)) {
    if(DEBUG) {
      Serial.print("OK");
      Serial.println();
      Serial.flush();
    }

    open_door();
    if(DEBUG){
      Serial.println("door has just been opened");
      Serial.flush();
    }

    msg[0] = 0x05;

    uint8_t h[LEN_HASH];
    hash.resetHMAC(K2, sizeof(K2));
    hash.update(ac, LEN_NONCE);
    hash.finalizeHMAC(K2, sizeof(K2), h, LEN_HASH);

    memcpy(msg+1, h, LEN_HASH);
    //msg[1+LEN_HASH] = 0x0;

    *reply_msg_len = 1 + LEN_HASH;
    
  } else {
    msg[0] = 0xff;
  }
}


void mdos_recv(uint8_t *in_msg, int in_msg_len, uint8_t *reply_msg, uint8_t *reply_msg_len) {

  if(DEBUG) {
    Serial.print("state: ");
    Serial.print(state);
    Serial.print(" received: ");
    serial_print_array(in_msg, in_msg_len);
    Serial.flush();
  }

  reply_msg[0] = 0xff;
  *reply_msg_len = 0;
  bool final_step = false;
  
  if(in_msg_len == 1 && in_msg[0] == 0x23) {
    if(DEBUG) {
      Serial.println("PING/PONG");
    }
    
    reply_msg[0] = 0x42;
    *reply_msg_len = 1;
  } else if (state == 0 && in_msg_len == 2 && in_msg[0] == 0x00 && in_msg[1] == 0x42) {
    start_protocol_tmr();
    process_pl_0(in_msg, reply_msg, reply_msg_len);
  } else if (state == 1 && in_msg_len == 50 && in_msg[0] == 0x02) {
    process_pl_2(in_msg, reply_msg, reply_msg_len);
  } else if (state == 2 && in_msg_len == 49 && in_msg[0] == 0x04) {
    process_pl_4(in_msg, reply_msg, reply_msg_len);
    final_step = true;
  }
  if (reply_msg[0] != 0xff) {
    //debug_led1(true);
    //debug_led2(true);

    // everything is fine, reply_msg is sent outside of this function

    //if (final_step) {
    //  reset();
    //}
  } else {
    disp_write_fail();
    debug_led1(false);
    debug_led2(true);
    start_relay_tmr(); // door is not open, but relay tmr also resets display
    //reset();
  }
}

void mdos_loop() {
  timer.run();
}

void mdos_setup() {
  pinMode(PIN_DEBUG_LED1, OUTPUT);
  pinMode(PIN_DEBUG_LED2, OUTPUT);
  pinMode(PIN_RAUMSTATUS_LED, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);

  switch_relay(false);
  
  hash = SHA256();

  Serial.begin(SERIAL_BAUD);
  
  //pinMode(LED, OUTPUT);

  RNG.begin("MDOS", 0);
  RNG.addNoiseSource(noise);

  disp_write_boot();
  start_relay_tmr();
}

