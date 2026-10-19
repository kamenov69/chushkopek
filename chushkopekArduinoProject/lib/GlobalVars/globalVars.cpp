#include <Arduino.h>
#include "Cmd.h"
#include "globalVars.h"



Vars globals;



float parse_float(int nargs, char **args){
//These parameters can also be passed to other functions like normal variables.
    float ret_value = 0.0;
  
    if((nargs > 0)){
      // Accept decimal values such as 0.0, 0.5 and 1.0.
      float  tmparg1 = strtof(args[0], nullptr);
      int  tmparg2 = 0;
      if (nargs > 1){ 
      tmparg2 =  cmdStr2Num(args[1], 10);
      }
      ret_value =  tmparg1*pow(10.0,tmparg2);
    }
    return ret_value;
  }

void _vars_update(int argc, char **args){
    if(argc > 1){
       VARS_TYPE_ tmp = (VARS_TYPE_)(parse_float(--argc, args+1));
       //--args;
       if( (globals.max_val(args[0]) - globals.min_val(args[0])) > (VARS_TYPE_)0.3){
            globals.set(args[0], tmp);
       }
      
    }
#ifdef VARS_TYPE_ == float
    cmdGetStream()->println(globals.get(args[0]),4);
#else
    cmdGetStream()->println(globals.get(args[0]));
#endif 
    
}


void _vars_list(int argc, char **args){
   for (auto* n = globals.head(); n != nullptr; n = n->next) {
       Stream *s = cmdGetStream();
       s->print(n->name_P);
       s->print(F(", "));
       s->print(n->value);
       s->print(F(", "));
       s->print(n->minVal);
       s->print(F(", "));
       s->print(n->maxVal);
       s->print(F(", "));
       s->println(n->updated);
    } 


}

void add_new_global_var(const char * name, VARS_TYPE_ value, VARS_TYPE_ min, VARS_TYPE_ max){
    globals.add(name, value, min, max);
    cmdAdd(name, _vars_update);

}


void setup_var_list_cmd(){cmdAdd("varlst", _vars_list);}

