#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>
#include <new>

template <typename T>
class VarList {
public:
  struct Node {
    char* name_P;   
    T value;
    T minVal;
    T maxVal;
    bool updated;
    Node* next;
  };

  VarList() : head_(nullptr) {};

  bool add(const char* name, T initial, T minVal, T maxVal) {
    if (!name) return false;
    if (findNode(name)) return false;
    Node* n = (Node*)malloc(sizeof(Node));
    if (!n) return false;
    size_t L = strlen(name);
    n->name_P = (char *)malloc(L+1);
    if (!n->name_P) 
    { free(n) ; 
      return false; 
    }
    strcpy(n->name_P,name);
    n->name_P[strlen(name)] = '\0';
    n->minVal = minVal;
    n->maxVal = maxVal;
    n->value  = clamp(initial, minVal, maxVal);
    n->updated = true;
    n->next = head_;
    head_ = n;
    return true;
  }
  
  char * get_name(){
    return this->name_P;
  }
  

  T get(const char* name_P)const{
        Node* n = findNode(name_P);
        if (!n) return false;
        //out = n->value;
        return n->value;
    }

   T min_val(const char* name_P)const{
        Node* n = findNode(name_P);
        if (!n) return false;
        return n->minVal;
    }

    T max_val(const char* name_P)const{
        Node* n = findNode(name_P);
        if (!n) return false;
        return n->maxVal;
    }


  bool set( const char* name_P, T v){
    Node* n = findNode(name_P);
    if (!n) return false;
    T nv = clamp(v, n->minVal, n->maxVal);
    if (nv != n->value) {
      n->value = nv;
      n->updated = true;
    }
    return true;
  }

  bool isUpdated(const char* name_P)const{
    Node* n = findNode(name_P);
    return n ? n->updated : false;
  }

  void clearUpdated(const char* name_P) {
    Node* n = findNode(name_P);
    if (n) n->updated = false;
  }

  Node* head() const { return head_; }

private:
  Node* head_;

  static T clamp(T v, T lo, T hi) {
    if ((hi - lo) <= (T) 0.3 ) return v;   //float ???
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
  }

  Node* findNode(const char* name_P)const{
    Node* cur = head_;
    while (cur) {
      if (strcmp(name_P, cur->name_P) == 0)
        return cur;
      cur = cur->next;
    }
    return nullptr;
  }
};
