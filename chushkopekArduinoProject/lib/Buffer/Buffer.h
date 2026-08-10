#ifndef __BUFFER_H_
#define __BUFFER_H_

#define ADDITIONAL_FUNK
template <typename T, size_t N>

class Buffer {

public:
   Buffer( bool c){
      cyclic =  c;
      in_index = 0;
   }
   
   void shift_left(){
       for(size_t i = 0; i < (buffer_size-1); i++){
          data[i] = data[i+1];
       }
   }
   
   void clear(void){
       in_index = 0;
   }
   
   size_t size(){return buffer_size;} 
   
   bool is_not_full(void){return in_index < buffer_size;}
   
   
   bool is_full(){
       if(cyclic) return false;
       else return in_index >= buffer_size;
   }
 

   void add(T dat){
       if( cyclic || (in_index < buffer_size)){
           if(in_index < buffer_size ) in_index++;
           shift_left();
           data[buffer_size-1] = dat;
       }
   }
 
   T get(size_t i){
      if(i>=buffer_size) i = i-buffer_size;
      return data[i];
   }
   
   T sum(void){
       T ret_sum = 0;
       for(size_t i=0; i< buffer_size; i++) ret_sum+=data[i];
       return ret_sum;
   }
     
   
   T  mean(){
       T ret_val = 0;
       for(size_t i=0; i< N; i++) ret_val+=(float)data[i];
       return (ret_val/buffer_size);
   }


#ifdef ADDITIONAL_FUNK
   float get_dt(void){return dt;}
   void  set_dt(float t){ dt = t;}
   float integral(void){ 
            //printf("integrall %f, %f \n\n",(float) sum(),dt);
            return (float)sum()*dt;
    }
    
    void revers_lin_reg(float *a, float *b){
    /*
       flaot a - slope
       float b - estimated historic last point
    */
            if (in_index != N) {
                *a = 0.0f;
                *b = 0.0f;
                return;
            }
            float sx = 0.0f;
            float sy = 0.0f;
            float sxx = 0.0f;
            float sxy = 0.0f;
            for(size_t i = 0; i < N; i++){      
                 float y = data[i];
                 float x = (N-1-i) * dt;
                 sx += x;
                 sy += y;
                 sxx += x * x;
                 sxy += x * y;
            } 
            float n = (float) in_index;
            float denom = n * sxx - sx * sx;
            if (denom == 0.0f) {
                *a = 0.0f;
                *b = sy / n;
                return;
            }

            *a = (n * sxy - sx * sy) / denom;
            *b = (sy - (*a) * sx) / n;
            *a = *a * (-1);
    }
   
   
#endif    
     T data[N];
private:
   
    size_t buffer_size = N;
    bool cyclic; 
    size_t in_index;
#ifdef ADDITIONAL_FUNK
    float dt=1;
#endif   
    
   
     
};

#endif
