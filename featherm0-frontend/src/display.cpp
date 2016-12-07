#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_LEDBackpack.h>
#include "config.h"

Adafruit_AlphaNum4 alpha4 = Adafruit_AlphaNum4();

void disp_write_num_reverse(int n) {

  int a = n;
  for (int i=0; i<4; i++) {
    int b = (a % 10);
    alpha4.writeDigitAscii(i, '0' + b);
    a = (a / 10);
  }
  alpha4.writeDisplay();
}

void disp_off() {
  for (int i = 0; i < 4; i++) 
    alpha4.writeDigitRaw(i, 0x0000);
  alpha4.writeDisplay();
}

void disp_write_open() {
  alpha4.writeDigitAscii(0, 'O');
  alpha4.writeDigitAscii(1, 'P');
  alpha4.writeDigitAscii(2, 'E');
  alpha4.writeDigitAscii(3, 'N');
  alpha4.writeDisplay();
}

void disp_write_fail() {
  alpha4.writeDigitAscii(0, 'F');
  alpha4.writeDigitAscii(1, 'A');
  alpha4.writeDigitAscii(2, 'I');
  alpha4.writeDigitAscii(3, 'L');
  alpha4.writeDisplay();
}

void disp_write_boot() {
  alpha4.writeDigitAscii(0, 'B');
  alpha4.writeDigitAscii(1, 'O');
  alpha4.writeDigitAscii(2, 'O');
  alpha4.writeDigitAscii(3, 'T');
  alpha4.writeDisplay();
}

void disp_setup() {
  alpha4.begin(DISP_ADDR);
  disp_off();
}  
