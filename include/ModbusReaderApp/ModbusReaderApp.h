#pragma once

#include <mutex>
#include <string>
#include <thread>

#include "modbusStack/mb_master.h"
#include "zeroMQ/ZMQClient.h"

using namespace std;

class ModbusReaderApp {
 private:
  // --- Hằng số cấu hình ---
  static constexpr const char* BROKER_ADDR = "ipc://test.ipc";
  static constexpr int SEND_INTERVAL_MS = 2000;
  static constexpr int RECONNECT_DELAY_S = 5;
  const std::string CLIENT_ID = "ModbusReader_01";  // Client ID cho ZMQ

  // --- Thành viên lớp ---
  ZMQClient m_zmqClient;
  ModbusMaster m_modbusMaster;

  std::thread m_senderThread;
  std::mutex m_mutex;

  bool m_stopFlag;
  bool m_isRunning;

  // --- Hàm xử lý nội bộ ---
  void senderRoutine();
  bool attemptReconnect();
  std::string readModbusData();

 public:
  // Constructor / Destructor
  ModbusReaderApp();
  ~ModbusReaderApp();

  // API công khai
  bool start();
  void stop();
  bool isRunning();
  void pollCommand(int timeout_ms);
};
