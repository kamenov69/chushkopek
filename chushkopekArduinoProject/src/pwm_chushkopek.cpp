#include <Arduino.h>
#include "board.h"
#include "globalVars.h"



void setup_pwm_pins(void){

    pinMode(pwm0_pin, OUTPUT);
    pinMode(pwm1_pin, OUTPUT);
    digitalWrite(pwm0_pin, LOW);
    digitalWrite(pwm1_pin, LOW);

    // Global resolution (0-1023)
    analogWriteResolution(10);//bits 
    // Pwm Frequency 
    analogWriteFrequency(1000);//kHz
    //analogWrite(PA8, 511); 50% 
    analogWrite(pwm0_pin, 0);       
    analogWrite(pwm1_pin, 0);       

    add_new_global_var("pwm0", 0, 0, 100);
    add_new_global_var("pwm1", 0, 0, 100);


}



void loop_pwm_pins(void){
    if(globals.isUpdated("pwm0")){
        globals.clearUpdated("pwm0");
        unsigned int int_valuse = (unsigned int)(globals.get("pwm0"));
        analogWrite(pwm0_pin, int_valuse);
    }
    
    if(globals.isUpdated("pwm1")){
        globals.clearUpdated("pwm1");
        unsigned int int_valuse = (unsigned int)(globals.get("pwm1"));
        analogWrite(pwm0_pin, int_valuse);
    }
}


