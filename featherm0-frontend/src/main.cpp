#include <Arduino.h>
#include "display.h"
#include "mdos.h"
#include "rf.h"

void setup(){
  disp_setup();
  mdos_setup();
  rf_setup();
}

void loop(){
  mdos_loop();
  rf_loop();
}

