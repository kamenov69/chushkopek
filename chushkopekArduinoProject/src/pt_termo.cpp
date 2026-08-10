#include <Arduino.h>
#include "Ticker.h"
#include "chushkopek_adc16.h"
#include "globalVars.h"
#include "Cmd.h"


// --- Pt50 ---
const float R0 = 42.5;               // Съпротивление при 0°C (Ома)
const float A = 3.9083e-3;           // Коефициент A
const float B = -5.775e-7;           // Коефициент B
const float R_REF = 613.0;           // Резистор в делителя (Ома)
const float V_CC_MV = 3300.0;        // Захранващо напрежение в миливолти (mV)

float Rpt50_to_real_toC(float v_pt50_mv, float r0 ){
    Stream *s=cmdGetStream();
    // Предпазване от грешни стойности
    if (v_pt50_mv <= 0 || v_pt50_mv >= V_CC_MV) {
      s->println("Error in Measurment of t!");
      return -3333;
    }

    // 2. R of PT50
    float R_pt50 = R_REF * (v_pt50_mv / (V_CC_MV - v_pt50_mv));

    // 3. Inversed quadratic polinom
    // $ B \cdot T^2 + A \cdot T + \left(1 - \frac{R}{R_0}\right) = 0$
    // T = (-A + sqrt(A^2 - 4*B*(1 - R/R0))) / (2*B)
    float discriminant = (A * A) - (4.0 * B * (1.0 - (R_pt50 / r0)));
    float temperature = 0.0;
    if (discriminant >= 0) {
        temperature = (-A + sqrt(discriminant)) / (2.0 * B);
    }else{
        s->println("dicriminant =0");
        return -3333;
    }
    return temperature;
}




void _temperature_task(void){
    float temperature =  Rpt50_to_real_toC(adc_get_buffer3(), R0);
    globals.set("t1", temperature);
}

Ticker tmr_tmperature(_temperature_task, 1000,0, MILLIS);

void setup_pt_termo(void){
    add_new_global_var("t1", 1, 0, 0);
    tmr_tmperature.start();
}

void loop_pt_termo(void){
    tmr_tmperature.update();
}

