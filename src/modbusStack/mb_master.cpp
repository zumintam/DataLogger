#include "../../include/modbusStack/mb_master.h"
// Implementation of Modbus master functionalities would go here
// For example, initializing the Modbus connection, reading/writing registers,
// etc. This is a placeholder for the actual implementation.

ModbusMaster::ModbusMaster() {
  // Constructor implementation
}

ModbusMaster::~ModbusMaster() {
  // Destructor implementation
}

modbus_t* ModbusMaster::create_rtu_ctx(uint8_t port) {
  // Create and return a Modbus RTU context for the specified port
  // Placeholder implementation
  return modbus_new_rtu(("/dev/ttyS" + std::to_string(port)).c_str(), 9600, 'N',
                        8, 1);
}
std::string ModbusMaster::dataString4Test() {
  // Sử dụng các giá trị cố định dưới dạng chuỗi để đảm bảo định dạng chính xác
  // (XX.XX)
  const std::string power = "400.00";
  const std::string temperature = "30.00";
  const std::string voltage = "220.50";

  // Tạo chuỗi thủ công bằng phép nối chuỗi (String Concatenation)
  std::string data = "Pwr:" + power + "kW" + "|Temp:" + temperature + "C" +
                     "|Vol:" + voltage + "V";

  return data;
}
