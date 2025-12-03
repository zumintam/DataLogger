#pragma once
#include <modbus/modbus.h>  // Thư viện libmodbus

#include <cstdint>
#include <ctime>
#include <iostream>
#include <sstream>
#include <string>

class ModbusMaster {
 public:
  ModbusMaster();
  ~ModbusMaster();

  // Modbus master functionalities would be declared here
  modbus_t* create_rtu_ctx(uint8_t port);
  std::string dataString4Test();
  std::string dataString4TestDB();
  bool connect() { return true; };  // Dummy connect function for illustration
};