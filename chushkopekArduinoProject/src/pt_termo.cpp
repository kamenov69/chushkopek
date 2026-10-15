#include <Arduino.h>
#include "Ticker.h"
#include "chushkopek_adc16.h"
#include "globalVars.h"
#include "Cmd.h"
#include "board.h"


#ifdef TS_PT_50
// --- Pt50 ---
const float R0 = 42.5;               // Съпротивление при 0°C (Ома)
const float A = 3.9083e-3;           // Коефициент A
const float B = -5.775e-7;           // Коефициент B
const float R_REF = 613.0;           // Резистор в делителя (Ома)
const float V_CC_MV = 3300.0;        // Захранващо напрежение в миливолти (mV)
#endif

#ifdef  TS_PT_100
const float R0 = 100.0;               // Съпротивление при 0°C (Ома)
const float A = 3.9083e-3;           // Коефициент A
const float B = -5.775e-7;           // Коефициент B
const float R_REF = 613.0;           // Резистор в делителя (Ома)
const float V_CC_MV = 3300.0;        // Захранващо напрежение в миливолти (mV)
#endif

constexpr float SENSOR_ERROR_TEMP = 3333.3;

float Rpt_to_real_toC(float v_pt_mv, float r0 ){
    Stream *s=cmdGetStream();
    // Предпазване от грешни стойности
    if (v_pt_mv <= 0 || v_pt_mv >= V_CC_MV) {
      s->println("Error in Measurment of t!");
      return SENSOR_ERROR_TEMP;
    }

    // 2. R of PT50
    float R_pt = R_REF * (v_pt_mv / (V_CC_MV - v_pt_mv));

    // 3. Inversed quadratic polinom
    // $ B \cdot T^2 + A \cdot T + \left(1 - \frac{R}{R_0}\right) = 0$
    // T = (-A + sqrt(A^2 - 4*B*(1 - R/R0))) / (2*B)
    float discriminant = (A * A) - (4.0 * B * (1.0 - (R_pt / r0)));
    float temperature = 0.0;
    if (discriminant >= 0) {
        temperature = (-A + sqrt(discriminant)) / (2.0 * B);
    }else{
        s->println("dicriminant =0");
        return SENSOR_ERROR_TEMP;
    }
    return temperature;
}



void _temperature_task(void){
    float temperature1 =  Rpt_to_real_toC(adc_get_buffer3(), R0);
    float temperature0 =  Rpt_to_real_toC(adc_get_buffer2(), R0);
    bool valid0 = temperature0 >= 3 && temperature0 <= 333;
    bool valid1 = temperature1 >= 3 && temperature1 <= 333;    
    if(valid1) globals.set("t1", temperature1); else globals.set("t1", SENSOR_ERROR_TEMP);   
    if(valid0) globals.set("t0", temperature0); else globals.set("t0", SENSOR_ERROR_TEMP);
}

Ticker tmr_tmperature(_temperature_task, 1000,0, MILLIS);

void setup_pt_termo(void){
    add_new_global_var("t0", 1, 0, 0);
    add_new_global_var("t1", 1, 0, 0);
    tmr_tmperature.start();
}

void loop_pt_termo(void){
    tmr_tmperature.update();
}

