#include <Arduino.h>
#include <Wire.h>

#include "config.h"

const unsigned char numbertable[] = { 0x3f,0x0c,
				      0x06,0x00,
				      0xdb,0x00,
				      0x8f,0x00,
				      0xe6,0x00,
				      0x69,0x20,
				      0xfd,0x00,
				      0x07,0x00,
				      0xff,0x00,
				      0xef,0x00 };

static unsigned char disp_str_off[] = { 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00 };
static unsigned char disp_str_open[] = { 0x00,0x3f,0x00,0xf3,0x00,0xf9,0x00,0x36,0x21 };
static unsigned char disp_str_fail[] = { 0x00,0x71,0x00,0xf7,0x00,0x00,0x12,0x38,0x00 };


void disp_write_raw_str(unsigned char* str) {
  Wire.beginTransmission(DISP_ADDR);
  Wire.write((char*) str);
  Wire.endTransmission();
}

void disp_write_raw_byte(byte str) {
  Wire.beginTransmission(DISP_ADDR);
  Wire.write(str);
  Wire.endTransmission();
}

void disp_write_num_reverse(int n) {
  unsigned char msg[9];

  int a = n;
  for (int i=0; i<4; i++) {
    int b = (a % 10);
    memcpy(msg+i*2, numbertable+b*2,2);
    a = b;
  }
  msg[8] = 0x0;

  disp_write_raw_str(msg);
}

void disp_off() {
  disp_write_raw_str(disp_str_off);
}

void disp_write_open() {
  disp_write_raw_str(disp_str_open);
}

void disp_write_fail() {
  disp_write_raw_str(disp_str_fail);
}


void disp_setup() {
  Wire.begin();

  // setup / turn on oscillator
  disp_write_raw_byte(0x21);

  // set blink off and enable display
  disp_write_raw_byte(0x81);

  // set display brightness to max
  disp_write_raw_byte(0xef);
}  
