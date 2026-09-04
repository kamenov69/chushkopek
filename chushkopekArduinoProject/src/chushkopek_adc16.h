#ifndef __CHUSKOPEK_ADC16_H
#define __CHUSKOPEK_ADC16_H

#define __NAME "Protecta"
#include <Arduino.h>
#include "ADS1115.h"
/*
#define ADS1115_RATE_8              0x00
#define ADS1115_RATE_16             0x01
#define ADS1115_RATE_32             0x02
#define ADS1115_RATE_64             0x03
#define ADS1115_RATE_128            0x04 // default
*/
//#define RATE ADS1115_RATE_32 
/*
#define ADS1115_PGA_6P144           0x00
#define ADS1115_PGA_4P096           0x01
#define ADS1115_PGA_2P048           0x02 // default
#define ADS1115_PGA_1P024           0x03
#define ADS1115_PGA_0P512           0x04
#define ADS1115_PGA_0P256           0x05
*/


/*

GAIN ADS1115_PGA_2P048 
bat-1689mV mes-1426.13   *1,1823  
bat-1689mV x10meas 150.5 *11.222

GAIN ADS1115_PGA_1P024
bat-1689mV     150.63   * 11.1929 

*/



#define GAIN ADS1115_PGA_1P024 
//#define GAIN ADS1115_PGA_2P048 
//#define ADC_PERIOD 1000/32       // 4 chan. 8 times in 1S every =  32 ADC readings

void setup_adc16();
void loop_adc16();

float adc_get_buffer2(void);
float adc_get_buffer3(void);

#endif