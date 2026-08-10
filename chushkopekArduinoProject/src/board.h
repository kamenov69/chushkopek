#ifndef __BOARD_H
#define __BOARD_H

#define __NAME "Protecta"
#include <Arduino.h>

// --- Pins Deffinitions 

//SCL   D15
//SDA   D14
//AVDD
//GND
#define LED  LED_BUILTIN //D13
#define BUTTON  PC13
#define alertReadyPin  D14
#define pwm0_pin  D6
#define pwm1_pin  D5


// --- Operation modes
#define MIN_MODE 0
#define MAX_MODE 3


#define LED_PERIOD 250  // ms



extern uint8_t mode;
void setup_board();
void loop_board();

#endif