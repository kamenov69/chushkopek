#include <Arduino.h>
#include "board.h"
#include "Ticker.h"
#include "Cmd.h"
#include "globalVars.h"


uint8_t _blinks = 1;


void _set_mode(int argn, char** args);
void _led_task(void);


uint8_t mode = 0;

Ticker ledTicker(_led_task, LED_PERIOD, 0, MILLIS);



void setup_board(){   
    //Serial.begin(9600);
    Serial.begin(115200);
 
    pinMode(LED_BUILTIN, OUTPUT); // Initialize the BUILTIN_LED pin as an output
    digitalWrite(LED_BUILTIN, LOW); // Turn the LED off by making the voltage LOW
    pinMode(BUTTON, INPUT_PULLUP);  // Blue Button
    cmdInit(&Serial);
    cmdAdd("hello", [](int argn, char** args){cmdGetStream()->println("Protecta");});
    cmdAdd("mode", _set_mode);
    //add_new_global_var("mode", mode, 0, 3);
    ledTicker.start();
}

void loop_board(){
    cmdPoll();
    ledTicker.update();
    if((mode+1) !=  _blinks) _blinks = mode+1;
    

    /*
    if (globals.isUpdated("mode")){
      globals.clearUpdated("mode");
      mode = (uint8_t)(globals.get("mode"));
      _blinks = mode+1;
    }
    */ 

}

void _set_mode(int argn, char** args){
    if(argn > 1){
        uint8_t m = atoi(args[1]);
        if(m >= MAX_MODE){
          m = MAX_MODE;
        }
        else if(m < MIN_MODE){
          m = MIN_MODE;
        }
        mode = m;       
    }
    cmdGetStream()->println(mode); 
}

void _led_task(void){
  static uint8_t temp_led_state = 0;
  if(temp_led_state){
      if((temp_led_state%2 == 0) &&  (temp_led_state > 2* _blinks)){
        digitalWrite(LED, HIGH);
      }
      else{
        digitalWrite(LED, LOW);
      }
      temp_led_state--; 
  }
  else{
       temp_led_state = 4 * _blinks; 
  }
}


