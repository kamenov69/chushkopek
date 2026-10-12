

/* v0.2

   main.cpp - Main loop for Arduino
   Part of SMILE project -

*/

#include <Arduino.h>
#include "board.h"
#include "globalVars.h"
#include "chushkopek_adc16.h"
#include "pt_termo.h"
#include "pwm_chushkopek.h"
#include "termo_controll.h"
#include "buzzer.h"

void setup() {
  setup_board();
  setup_adc16();
  
  setup_pt_termo();
  setup_pwm_pins();
  
  setup_termo_controll();
  setup_buzzer();

  setup_var_list_cmd(); // must be last!
}

void loop() {
  loop_board();
  loop_adc16();
  loop_pt_termo();
  loop_pwm_pins(); 
  loop_termo_controll();
  loop_buzzer();

}