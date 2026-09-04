#include "chushkopek_adc16.h"
#include "board.h"
#include "Buffer.h"
#include "Cmd.h"
#include "Ticker.h"
#include "globalVars.h" 

Buffer<float, 64> buffer0(false);// 8 times in second x 8 seconds -  not cyclick   
Buffer<float, 64> buffer1(false);// 
Buffer<float, 8> buffer2(true); //  1 second cyclick 
Buffer<float, 8> buffer3(true); //  1 second cyclic  

ADS1115 adc(ADS1115_DEFAULT_ADDRESS);

void print_buffer(float *buf, size_t max_index){
    Stream  *s = cmdGetStream();
    for(size_t i=0; i<max_index; i++){
        s->print(buf[i],4);
        if(i != max_index -1)s->print(", ");
    }
    s->println();
}


static const uint8_t muxes[] = {
    ADS1115_MUX_P0_NG,
    ADS1115_MUX_P1_NG,
    ADS1115_MUX_P2_NG,
    ADS1115_MUX_P3_NG
};

void _adc_task()
{
    static uint8_t channel = 0;

    // Проверка без блокиращо чакане
    if (!adc.isConversionReady()) {
        return;
    }

    float value = adc.getMilliVolts();

    switch (channel) {
        case 0: buffer0.add(value); break;
        case 1: buffer1.add(value); break;
        case 2: buffer2.add(value); break;
        case 3: buffer3.add(value); break;
    }

    channel = (channel + 1) % 4;

    // Настройване на следващия канал
    adc.setMultiplexer(muxes[channel]);

    // Стартиране на следващата конверсия
    adc.triggerConversion();

    if( buffer0.is_full() && buffer1.is_full() ){
        globals.set("crdy",1.0);
        mode = 0;
    }


    if( !digitalRead(BUTTON)  && globals.get("crdy")) {
        mode =1;
        buffer0.clear();
        buffer1.clear();
        globals.set("crdy",0.0);
    }

}


Ticker adc_timer(_adc_task,1, 0, MILLIS); //every mS  ADC_PERIOD

void setup_adc16(){
    //Wire.setClock();
    Wire.begin();
    //Wire.setClock(10000);
    Serial.println("Testing device connections...");
    Serial.println(adc.testConnection() ? "ADS1115 connection successful" : "ADS1115 connection failed");  
    adc.initialize(); // initialize ADS1115 16 bit A/D chip
    // We're going to do single shot sampling
    adc.setMode(ADS1115_MODE_SINGLESHOT);
    // Slow things down so that we can see that the "poll for conversion" code works
    adc.setRate(ADS1115_RATE_32);  //  
    // Set the gain (PGA) +/- 6.144v
    // Note that any analog input must be higher than –0.3V and less than VDD +0.3
    adc.setGain(GAIN);
    // ALERT/RDY pin will indicate when conversion is ready
    //pinMode(alertReadyPin,INPUT_PULLUP);
    //adc.setConversionReadyPinMode();
    adc.setMultiplexer(ADS1115_MUX_P0_NG);
    adc.triggerConversion();
    cmdAdd("buf0", [](int, char**){print_buffer(buffer0.data, buffer0.size());});
    cmdAdd("buf1", [](int, char**){print_buffer(buffer1.data, buffer1.size());});
    cmdAdd("buf2", [](int, char**){print_buffer(buffer2.data, buffer2.size());});
    cmdAdd("buf3", [](int, char**){print_buffer(buffer3.data, buffer3.size());});
 //   cmdAdd("int0", [](int, char**){cmdGetStream()->println(buffer0.integral(),4);});
 //   cmdAdd("int1", [](int, char**){cmdGetStream()->println(buffer1.integral(),4);});
    cmdAdd("sum0", [](int, char**){cmdGetStream()->println(buffer0.sum(),4);});
    cmdAdd("sum1", [](int, char**){cmdGetStream()->println(buffer1.sum(),4);});
    cmdAdd("sum2", [](int, char**){cmdGetStream()->println(buffer2.sum(),4);});
    cmdAdd("sum3", [](int, char**){cmdGetStream()->println(buffer3.sum(),4);});
 //   cmdAdd("mean2", [](int, char**){cmdGetStream()->println(buffer2.mean(),4);});
 //   cmdAdd("mean3", [](int, char**){cmdGetStream()->println(buffer3.mean(),4);});
    cmdAdd("adctst", [](int , char **){cmdGetStream()->println(adc.testConnection() ? "ADC OK" : "ADC NOTOK");});
    cmdAdd("adcclr", [](int, char **){
        mode =1;
        buffer0.clear();
        buffer1.clear();
        globals.set("crdy",0.0);
        cmdGetStream()->println("1");
        cmdGetStream()->println();
    });

    adc_timer.start();
    add_new_global_var("crdy", 1, 0, 0);
    //add_new_global_var("mean_c2", 0, 0, 0);
    //add_new_global_var("mean_c3", 0, 0, 0);
    
}


void loop_adc16(){
    adc_timer.update();

}

float adc_get_buffer2(void){return buffer2.mean();}
float adc_get_buffer3(void){return buffer3.mean();}