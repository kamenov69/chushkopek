#include "chushkopek_adc16.h"
#include "board.h"
#include "Buffer.h"
#include "Cmd.h"
#include "Ticker.h"
#include "globalVars.h" 
//#include "buzzer.h"

Buffer<float, MEASUREMENT_BUFFER_SIZE> buffer0(false);// not cyclic
Buffer<float, MEASUREMENT_BUFFER_SIZE> buffer1(false);// not cyclic
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

void _button_task(){
    // These variables implement a one-shot edge detector.  Once the input has
    // stayed inactive for the configured time, that qualification is retained
    // across short active pulses.  This means a short pulse cancels only its
    // own attempt; the next longer active pulse can be accepted immediately.
    static bool inactiveTimerRunning = false;
    static bool inactiveQualified = false;
    static bool activeHoldPending = false;
    static uint32_t inactiveSince = 0;
    static uint32_t activeSince = 0;

    // BUTTON_TRIGGER_LEVEL is configurable in board.h, so the same code
    // supports both HIGH -> LOW and LOW -> HIGH measurement triggers.
    const bool buttonIsActive = (digitalRead(BUTTON) == BUTTON_TRIGGER_LEVEL);

    if (!buttonIsActive) {
        // A short active pulse cancels only the active hold timer.  Keep
        // inactiveQualified true so another active pulse does not need to
        // wait for BUTTON_STABLE_TIME_MS again.
        activeHoldPending = false;

        // Start the inactive-level timer only when the input has not already
        // been qualified.  After a completed measurement this also rearms the
        // detector for the next inactive-to-active cycle.
        if (!inactiveQualified && !inactiveTimerRunning) {
            inactiveSince = millis();
            inactiveTimerRunning = true;
        }
        return;
    }

    // Detect the transition to the active level only after the input has
    // remained inactive for BUTTON_STABLE_TIME_MS.  The measurement is not
    // started yet: the active level must now be held for another interval.
    if (!inactiveQualified && inactiveTimerRunning) {
        if ((uint32_t)(millis() - inactiveSince) < BUTTON_STABLE_TIME_MS) {
            // The inactive level was too short, so this is not a valid cycle.
            inactiveTimerRunning = false;
            return;
        }

        // Remember that the inactive level has already been valid long enough.
        // This qualification survives a short active pulse below.
        inactiveTimerRunning = false;
        inactiveQualified = true;
        activeSince = millis();
        activeHoldPending = true;
        return;
    }

    // A later active pulse starts a fresh active hold, while retaining the
    // previously acquired inactive qualification.
    if (inactiveQualified && !activeHoldPending) {
        activeSince = millis();
        activeHoldPending = true;
        return;
    }

    // Start the measurement only after the active level has been held for the
    // configured pause.  Returning inactive before this point cancels it.
    if (inactiveQualified && activeHoldPending &&
        (uint32_t)(millis() - activeSince) >= BUTTON_ACTIVE_HOLD_TIME_MS) {
        // Keep the existing measurement-start actions: stop the ready state
        // and clear both non-cyclic measurement buffers.
        mode = 1;
        buffer0.clear();
        buffer1.clear();
        globals.set("crdy", 0.0);
        activeHoldPending = false;
        // Require a new inactive period after a successful measurement before
        // accepting another active transition.
        inactiveQualified = false;
    }

    // If the active level drops before the hold time expires, the inactive
    // branch above cancels only activeHoldPending and preserves the qualification.
}




void _adc_task()
{
    static uint8_t channel = 0;

    _button_task();

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
