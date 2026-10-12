#include <Arduino.h>
#include "board.h"
#include "Ticker.h"
#include "chushkopek_adc16.h"
#include "globalVars.h"
#include "Cmd.h"

void stop_buzz(void){digitalWrite(buzzer_pin,LOW);}
Ticker stop_buzzer_tiemr(stop_buzz, 200, 1, MILLIS);
void peep(){
    digitalWrite(buzzer_pin,HIGH);
    stop_buzzer_tiemr.start();
}

void setup_buzzer(){
    pinMode(buzzer_pin, OUTPUT);
    digitalWrite(buzzer_pin,HIGH);
    delay(100);
    digitalWrite(buzzer_pin,LOW);

    cmdAdd("peep",
            [](int cnt, char** args){
                peep();
                cmdGetStream()->println(1);
            });
}



void loop_buzzer(){
static int old_redy_flag;

int tmp = globals.get("crdy");
    if (tmp != old_redy_flag){
        if(tmp == 1){
            peep();
        }
        old_redy_flag = tmp;
    }   


    stop_buzzer_tiemr.update();
}