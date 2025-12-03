#pragma once

#include <mutex>
#include <string>
#include <thread>

#include "modbusStack/mb_master.h"
#include "zeroMQ/ZMQClient.h"

// Sử dụng namespace std để tránh viết std:: liên tục trong file header
using namespace std;

class ModbusReaderApp {
 private:
  // --- 1. HẰNG SỐ (Khởi tạo trước) ---
  // Đảm bảo là static constexpr để được khởi tạo trước mọi thành viên khác
  static constexpr const char* BROKER_ADDR = "ipc://test.ipc";
  static constexpr int SEND_INTERVAL_MS = 2000;
  static constexpr int RECONNECT_DELAY_S = 5;
  const std::string CLIENT_ID = "ModbusReader_01";  // ID bắt buộc cho ZMQClient

  // --- 2. THÀNH VIÊN LỚP ---
  // Khai báo thành viên ZMQ và Modbus trước để thứ tự khởi tạo được đảm bảo.
  // Lỗi bad_alloc nằm ở đây nếu chúng không được khai báo đúng.
  ZMQClient m_zmqClient;
  ModbusMaster m_modbusMaster;

  // Các thành viên cho đa luồng và trạng thái
  std::thread m_senderThread;
  std::mutex m_mutex;
  bool m_stopFlag;
  bool m_isRunning;

  // --- 3. CÁC HÀM HỖ TRỢ ---
  void senderRoutine();
  bool attemptReconnect();
  std::string readModbusData();

 public:
  // Constructor (đã được định nghĩa trong .cpp)
  ModbusReaderApp();

  // Destructor (đã được định nghĩa trong .cpp)
  ~ModbusReaderApp();

  // Các hàm công khai
  bool start();
  void stop();
  bool isRunning();
  void pollCommand(int timeout_ms);
};