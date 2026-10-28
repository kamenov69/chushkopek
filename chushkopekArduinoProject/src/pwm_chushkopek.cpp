#include <Arduino.h>
#include "board.h"
#include "globalVars.h"

// Enforce the board limit at the hardware output, regardless of the source.
static unsigned int limited_pwm(float value){
    if (!(value > 0.0f)) return 0; // Negative values and NaN also turn heating off.
    if (value > PWM_MAX_VALUE) return PWM_MAX_VALUE;
    return (unsigned int)value;
}


void setup_pwm_pins(void){

    pinMode(pwm0_pin, OUTPUT);
    pinMode(pwm1_pin, OUTPUT);
    digitalWrite(pwm0_pin, LOW);
    digitalWrite(pwm1_pin, LOW);

    // Global resolution (0-1023)
    analogWriteResolution(10);//bits 
    // Pwm Frequency 
    analogWriteFrequency(1000);//kHz
    analogWrite(pwm0_pin, 0);       
    analogWrite(pwm1_pin, 0);       

    add_new_global_var("pwm0", 0, PWM_MIN_VALUE, PWM_MAX_VALUE);
    add_new_global_var("pwm1", 0, PWM_MIN_VALUE, PWM_MAX_VALUE);


}



void loop_pwm_pins(void){
    if(globals.isUpdated("pwm0")){
        globals.clearUpdated("pwm0");
        analogWrite(pwm0_pin, limited_pwm(globals.get("pwm0")));
    }
    
    if(globals.isUpdated("pwm1")){
        globals.clearUpdated("pwm1");
        analogWrite(pwm1_pin, limited_pwm(globals.get("pwm1")));
    }
}


