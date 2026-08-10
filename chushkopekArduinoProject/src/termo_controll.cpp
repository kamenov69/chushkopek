#include <Arduino.h>
#include "board.h"
#include "globalVars.h"
#include <PID_v1.h>
#include "Cmd.h"

//Define Variables we'll be connecting to
float Setpoint1, Input1, Output1;
float Setpoint0, Input0, Output0;


// On/Off experimetn with the solder airon heatter  
// Tu = 15c
// tmax-tmin = 13C a = 13/2 =6.5C
// (bmin - bmax)/2   = 100%-0% = 50%  max heating 100 unists form 1023  Pudsed = 10% Pallowed 
// Kcritical = 4*a/(3.1425 *b) = 9.79 creytical ampl. coeficent 

// Very conservativ settings
float Kp= 1.96;       // Kp = 0.2 Kcritical =  1.96
float Ki= Kp/7.5;     // ti = Tu/2 = 7.5     Ki = Kp/ti = 0.26 
float Kd= Kp*Ki*2/3;  // td = Tu/3 = 2/3*ti  Kd = Kp*td = 9.79 


PID PID1(&Input1, &Output1, &Setpoint1, Kp, Ki, Kd, 0);
PID PID0(&Input0, &Output0, &Setpoint0, Kp, Ki, Kd, 0);
void update_pid(){
      
  Kp = globals.get("kp");
  float tmp = globals.get("tau");
  if(tmp != 0.0 ){
    Ki = (Kp)/tmp; 
    //Kd = Kp*0.25*tmp;
    Kd = Kp*tmp*2/3;
  } 
  else{
    Ki = 0; Kd = 0;
  } 
  PID0.SetTunings(Kp,Ki,Kd);  
  PID1.SetTunings(Kp,Ki,Kd);
}

void setup_termo_controll(){
  //initialize the variables we're linked to
  Input1 = globals.get("t1");
  Input1 = globals.get("t0");
  
  PID0.SetOutputLimits(0.0, 100.0);
  PID1.SetOutputLimits(0.0, 100.0);
  PID0.SetSampleTime(1000);
  PID1.SetSampleTime(1000);
  Setpoint0 = 100;
  Setpoint1 = 100;
 
  add_new_global_var("sp0", 100, 0, 370);
  add_new_global_var("sp1", 100, 0, 370);
  add_new_global_var("kp", Kp, 0.01, 1000);
  add_new_global_var("tau", Kp/Ki, 0.05, 600.0);
  add_new_global_var("pid0m", 0, 0.0, 1.0);
  add_new_global_var("pid1m", 0, 0.0, 1.0);

   //turn the PID off
  PID0.SetMode(MANUAL);
  PID1.SetMode(MANUAL);

  update_pid();

  cmdAdd("pid", [](int cnt, char **args){
    Stream *s = cmdGetStream();
    s->print(Kp);s->print(", ");  
    s->print(Ki);s->print(", "); 
    s->println(Kd);
    s->println();
  });
}



void update_param(void){
    if(globals.isUpdated("sp0")){
      Setpoint0 = globals.get("sp0");
      globals.clearUpdated("sp0");
    }
    if(globals.isUpdated("sp1")){
      Setpoint1 = globals.get("sp1");
      globals.clearUpdated("sp1");
    }

    if(globals.isUpdated("kp")){
      globals.clearUpdated("kp");
      update_pid();
      
    }

    if(globals.isUpdated("tau")){
      globals.clearUpdated("tau");
      update_pid();
    }

    if(globals.isUpdated("pid0m")){
      if(globals.get("pid0m") == 0) {PID0.SetMode(MANUAL); globals.set("pwm0", 0);}
      else PID0.SetMode(AUTOMATIC);
      globals.clearUpdated("pid0m");
    }

    if(globals.isUpdated("pid1m")){
      if(globals.get("pid1m") == 0){ PID1.SetMode(MANUAL); globals.set("pwm1", 0);} 
      else PID1.SetMode(AUTOMATIC);
      globals.clearUpdated("pid1m");
    }


}

void loop_termo_controll(){
  update_param();
  Input0 = globals.get("t0");
  Input1 = globals.get("t1");
  PID0.Compute();
  PID1.Compute();
  if(PID0.GetMode()) globals.set("pwm0", Output0 );
  if(PID1.GetMode()) globals.set("pwm1", Output1 );
}





