#pragma once
#include <modbus/modbus.h>  // Thư viện libmodbus

#include <cstdint>
#include <iostream>
#include <string>

class ModbusMaster {
 public:
  ModbusMaster();
  ~ModbusMaster();

  // Modbus master functionalities would be declared here
  modbus_t* create_rtu_ctx(uint8_t port);
  std::string dataString4Test();
  bool connect() { return true; };  // Dummy connect function for illustration
};