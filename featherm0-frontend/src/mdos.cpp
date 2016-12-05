#include <Crypto.h>
#include <SHA256.h>
#include <SimpleTimer.h>
#include "display.h"

#define LED           13  // onboard blinky

#define DEBUG true

#define CNT_RAND_INSECURE_SEED 0x0000
#define RELAY_TIMEOUT 3000
#define PROTOCOL_TIMEOUT 60000

static char k0[] = { 0x00, 0x01 };
static char k1[] = { 0x00, 0x01 };
static char k2[] = { 0x00, 0x01 };

#define PROTOCOL_TIMER 1
#define RELAY_TIMER 0
#define PIN_DEBUG_LED 1
#define PIN_RELAY 2

#define LEN_NONCE 16
#define LEN_HASH 32
#define LEN_PC 4

SimpleTimer timer;
SHA256 hash;

int state;
char tc[LEN_NONCE];
char nc[LEN_NONCE];
char oc[LEN_NONCE];
char pc[LEN_PC];

int relay_timer_id;
int protocol_timer_id;


void mdos_setup() {
  pinMode(PIN_DEBUG_LED, OUTPUT);
  hash = SHA256();

  Serial.begin(SERIAL_BAUD);
  
  //pinMode(LED, OUTPUT);
}


void debug_led(bool state) {
  if (state) {
    digitalWrite(PIN_DEBUG_LED, HIGH);
  } else {
    digitalWrite(PIN_DEBUG_LED, LOW);
  }
}

void switch_relay(bool state) {
  if (state) {
    digitalWrite(PIN_RELAY, HIGH);
  } else {
    digitalWrite(PIN_RELAY, LOW);
  }
}

void reset() {
if (timer.isEnabled(protocol_timer_id)) {
  timer.disable(protocol_timer_id);
}

 state = 0;
 tc[0] = 0; // is this a good idea? -> I need some NULL replacement here
 nc[0] = 0;
 oc[0] = 0;
 pc[0] = 0;

 debug_led(false);
}

void protocol_tmr_handler() {
  reset();
  disp_off();
}

void start_protocol_tmr() {
  protocol_timer_id = timer.setTimeout(PROTOCOL_TIMEOUT, protocol_tmr_handler);
  // enable? -> check source code
}

void relay_tmr_handler() {
  switch_relay(false);
  // do we need to reset the timer? -> check source code
  disp_off();
}

void start_relay_tmr() {
  relay_timer_id = timer.setTimeout(RELAY_TIMEOUT, relay_tmr_handler);
  // enable? -> check source code
}

void open_door() {
  // set pin 1 high (in lua code). what is the equivalent here -> check
  disp_write_open();
  start_relay_tmr();
}


void rand_insecure(char* dest) {
  // TODO: use crypto lib RNG perhaps?
}

void rand_secure(char* dest) {
  // TODO: use crypto lib RNG perhap?s
}


void process_pl_0(char *pl, char *msg) {
  if(DEBUG) {
    Serial.print("0: ");
  }

  rand_insecure(tc);

  if(DEBUG) {
    Serial.print("tc=");
    Serial.print(tc);
  }

  msg[0] = 0x01;
  memcpy(msg+1, tc, LEN_NONCE);
  msg[1+LEN_NONCE] = 0x0;

  state++;
}

void process_pl_2(char *pl, char *msg) {
  if(DEBUG) {
    Serial.print("2: ");
  }

  byte mode = pl[1];
  memcpy(nc, pl+2, LEN_NONCE);
  char h_rec[LEN_HASH];
  memcpy(h_rec, pl+17, LEN_HASH);
  char h_own[LEN_HASH];
  hash.resetHMAC(k0, sizeof(k0));
  hash.update(tc, LEN_NONCE);
  hash.update(pl+1, sizeof(mode));
  hash.update(nc, LEN_NONCE);
  hash.finalizeHMAC(k0, sizeof(k0), h_own, LEN_HASH);

  // add some debug output here

  if (!strcmp(h_own, h_rec)) {
    relay_tmr_handler(); // reset timer

    rand_secure(oc);

    if(DEBUG) {
      Serial.print("oc=");
      Serial.print(oc);
    }
    
    msg[0] = 0x03;

    if (mode == 0x01) {
      // generate presence challenge
      char pc_src[LEN_NONCE];
      rand_secure(pc_src);
      long pc_num = (pc_src[0]*256 + pc_src[1]) % 10000;
      disp_write_num_reverse(pc_num);
      for (int i = 0; i<4; i++) {
	pc[i] = pc_num % 10;
	pc_num = pc_num / 10;
      }
    } else {
      // CURRENTLY DISABLED
      // no presence challenge
      memset(pc, 0xff, LEN_PC);
      msg[0] = 0x00; // invalidate msg
    }

    memcpy(msg+1, oc, LEN_NONCE);
    msg[1+LEN_NONCE] = 0x0;
    
    state++;
  } else {
    msg[0] = 0x0;
  }
}

void process_pl_4(char *pl, char *msg) {
  if(DEBUG) {
    Serial.print("4: ");
  }

  char ac[LEN_NONCE];
  memcpy(ac, pl+1, LEN_NONCE);

  char h_rec[LEN_HASH];
  memcpy(h_rec, pl+17, LEN_HASH);
  char h_own[LEN_HASH];
  hash.resetHMAC(k1, sizeof(k1));
  hash.update(nc, LEN_NONCE);
  hash.update(pc, LEN_PC);
  hash.update(oc, LEN_NONCE);
  hash.update(ac, LEN_NONCE);
  hash.finalizeHMAC(k1, sizeof(k1), h_own, LEN_HASH);

  if (!strcmp(h_own, h_rec)) {
    if(DEBUG) {
      Serial.print("OK");
    }

    open_door();

    msg[0] = 0x05;

    char h[LEN_HASH];
    hash.resetHMAC(k2, sizeof(k2));
    hash.update(ac, LEN_NONCE);
    hash.finalizeHMAC(k2, sizeof(k2), h, LEN_HASH);

    memcpy(msg+1, h, LEN_HASH);
    msg[1+LEN_HASH] = 0x0;
    
  } else {
    msg[0] = 0x0;
  }
}


void recv(char *pl) {

  char msg[50];
  msg[0] = 0x00;
  bool final_step = false;
  
  if(DEBUG) {
    Serial.print("state: ");
    Serial.print(state);
    Serial.print(" received: ");
    Serial.println(pl);
  }

  if(strlen(pl) == 1 && pl[0] == 0x23) {
    if(DEBUG) {
      Serial.println("PING/PONG");
    }
    
    strcpy(msg, "\x42");
  } else if (state == 0 && strlen(pl) == 2 && pl[0] == 0x00 && pl[1] == 0x42) {
    start_protocol_tmr();
    process_pl_0(pl, msg);
  } else if (state == 1 && strlen(pl) == 50 && pl[0] == 0x02) {
    process_pl_2(pl, msg);
  } else if (state == 2 && strlen(pl) == 49 && pl[0] == 0x04) {
    process_pl_4(pl, msg);
    final_step = true;
  }
  if (msg[0] == 0x00) {
    debug_led(true);

    // send msg -> TODO

    if (final_step) {
      reset();
    }
  } else {
    disp_write_fail();
    start_relay_tmr();
    reset();
  }
}
