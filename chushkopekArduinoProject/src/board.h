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
#define buzzer_pin  D7
#define pwm0_pin  D6
#define pwm1_pin  D5


// --- Operation modes
#define MIN_MODE 0
#define MAX_MODE 3


#define LED_PERIOD 250  // ms



extern uint8_t mode;
void setup_board();
void loop_board();


// --- PID_CONTROL_LIMITS

#define PWM_MAX_VALUE 100
#define PWM_MIN_VALUE 0 
// Very conservativ settings
#define  PID_KP_INIT  1.96                        // Kp = 0.2 Kcritical =  1.96
#define  PID_KI_INIT  (PID_KP_INIT) / 7.5              // ti = Tu/2 = 7.5     Ki = Kp/ti = 0.26 
#define  PID_KD_INIT  (PID_KP_INIT * PID_KI_INIT) * 2/3  // td = Tu/3 = 2/3*ti  Kd = Kp*td = 9.79 


#endif