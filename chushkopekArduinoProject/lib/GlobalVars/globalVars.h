#pragma once
#include <Arduino.h>
#include "VarList.h"

//#define VARS_TYPE_  int
#define VARS_TYPE_  float
using Vars = VarList<VARS_TYPE_>;   // 
extern Vars globals;
void add_new_global_var(const char *, VARS_TYPE_ , VARS_TYPE_ , VARS_TYPE_ );
void setup_var_list_cmd();
