#include <Arduino.h>
#include "../lib/arduinolibs/libraries/Crypto/Crypto.h"
#include "../lib/SimpleTimer/SimpleTimer.h"
#include "display.h"



#define CNT_RAND_INSECURE_SEED 0x0000
#define RELAY_TIMEOUT 3000
#define PROTOCOL_TIMEOUT 60000

#define PROTOCOL_TIMER 1
#define RELAY_TIMER 0
#define PIN_DEBUG_LED 1
#define PIN_RELAY 2

SimpleTimer timer;

int state;
int tc, nc, oc, pc, mode;

int relay_timer_id;
int protocol_timer_id;


void mdos_setup() {
  pinMode(PIN_DEBUG_LED, OUTPUT);
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
 tc = 0;
 nc = 0;
 oc = 0;
 pc = 0;
 mode = 0;

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





void process_pl_0(char *pl) {
  
}
