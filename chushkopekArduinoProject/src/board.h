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

// --- Measurement trigger configuration
// The input must remain at the inactive level for this amount of time before
// the configured transition is accepted as a new measurement request.
// This replaces the old implicit value of approximately 1000 loop calls.
#define BUTTON_STABLE_TIME_MS 1000

// After the trigger transition is detected, the active level must remain
// present for this additional time before the measurement is started.
#define BUTTON_ACTIVE_HOLD_TIME_MS 100

// Select the level that starts a measurement when the input transitions to it.
// LOW  = current behaviour: wait at HIGH, then trigger on HIGH -> LOW.
// HIGH = reverse behaviour: wait at LOW, then trigger on LOW -> HIGH.
#define BUTTON_TRIGGER_LEVEL HIGH


// --- Operation modes
#define MIN_MODE 0
#define MAX_MODE 3


#define LED_PERIOD 250  // ms



extern uint8_t mode;
void setup_board();
void loop_board();


// --- PID CONTROL
// Termo sensor 
// --- PT50 or PT100
//#define TS_PT_50
//#define REFF_RESISDTOR_Ohms  613.0
#define TS_PT_100  
#define REFF_RESISDTOR_Ohms 1003.0



// --- Maximum allowed PWM duty (10-bit hardware range: 0-1023).
// Shared by manual PWM commands, PID and on/off control.
// 100 = ~9.8%, 512 = ~50%, 1023 = 100% of the hardware range.
#define PWM_MAX_VALUE 1023
#define PWM_MIN_VALUE 0 

#if PWM_MAX_VALUE <= PWM_MIN_VALUE || PWM_MAX_VALUE > 1023
#error "PWM_MAX_VALUE must be between 1 and 1023"
#endif

// Very conservativ settings
#define  PID_KP_INIT     50                  // 1.96 Kp = 0.2 Kcritical =  1.96
#define  PID_KI_INIT  (PID_KP_INIT) / 15  // ti = Tu/2 = 7.5     
                                           // Ki = Kp/ti = 0.26 
#define  PID_KD_INIT  (PID_KP_INIT * PID_KI_INIT) * 2/3  // td = Tu/3 = 2/3*ti  

#endif
