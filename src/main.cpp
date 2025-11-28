#include <chrono>
#include <iostream>
#include <thread>

#include "ModbusReaderApp/ModbusReaderApp.h"  // Nhúng file quản lý ứng dụng

using namespace std;

int main() {
  cout << "========================================" << endl;
  cout << "   MODBUS READER SERVICE (C++ / ZMQ)    " << endl;
  cout << "========================================" << endl;

  // 1. Khởi tạo Đối tượng Ứng dụng
  // Toàn bộ logic khởi tạo ZMQ, Modbus, và Mutex nằm trong lớp này
  ModbusReaderApp app;

  // 2. Bắt đầu chạy
  // Hàm start() sẽ thiết lập kết nối và khởi động Sender Thread (đa luồng)
  if (!app.start()) {
    cerr << "[FATAL] Khong the khoi dong ung dung. Kiem tra log." << endl;
    return -1;
  }

  // 3. Vòng lặp chính (Main Loop)
  // Giữ chương trình chạy và lắng nghe lệnh điều khiển từ Broker
  while (app.isRunning()) {
    // Main thread lắng nghe lệnh (polling) từ Broker để duy trì phản hồi nhanh
    app.pollCommand(100);

    // Ngủ nhẹ để giảm tải CPU hệ thống
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }

  // Hàm destructor của 'app' sẽ tự động gọi stop() và join thread.

  cout << "========================================" << endl;
  cout << "   SERVICE STOPPED SUCCESSFULLY         " << endl;
  cout << "========================================" << endl;

  return 0;
}