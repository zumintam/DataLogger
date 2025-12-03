#include "../../include/ModbusReaderApp/ModbusReaderApp.h"

#include <chrono>
#include <iostream>
#include <thread>

using namespace std;

// Constructor

// Constructor
ModbusReaderApp::ModbusReaderApp()
    // LỖI CŨ: : m_zmqClient(BROKER_ADDR), m_stopFlag(false), m_isRunning(false)
    // {}

    // SỬA LỖI: Cung cấp cả BROKER_ADDR và CLIENT_ID
    : m_zmqClient(BROKER_ADDR, CLIENT_ID),
      m_stopFlag(false),
      m_isRunning(false) {}
// Destructor: Quan trọng để gọi stop() và join thread
ModbusReaderApp::~ModbusReaderApp() { stop(); }

bool ModbusReaderApp::start() {
  cout << "[APP] Dang khoi dong Modbus Reader..." << endl;

  // 1. Kết nối Modbus (Sử dụng API ModbusMaster)
  // Giả định hàm connect() sẽ trả về true nếu thành công
  if (!m_modbusMaster.connect()) {
    cerr << "[APP] ERROR: Khong the ket noi thiet bi Modbus!" << endl;
    return false;
  }

  // 2. Thiết lập trạng thái chạy an toàn
  {
    lock_guard<mutex> lock(m_mutex);
    m_stopFlag = false;
    m_isRunning = true;
  }

  // 3. Bắt đầu luồng gửi (Worker Thread)
  m_senderThread = std::thread(&ModbusReaderApp::senderRoutine, this);

  cout << "[APP] Khoi dong thanh cong. Sender thread dang chay." << endl;
  return true;
}

void ModbusReaderApp::stop() {
  // Đặt cờ dừng an toàn (Monitor Pattern)
  {
    lock_guard<mutex> lock(m_mutex);
    if (!m_isRunning) return;
    m_stopFlag = true;
    m_isRunning = false;
  }
  cout << "[APP] Dang yeu cau dung..." << endl;

  // Chờ luồng phụ kết thúc (Join)
  if (m_senderThread.joinable()) {
    m_senderThread.join();
  }
  cout << "[APP] Da dung hoan toan." << endl;
}

bool ModbusReaderApp::isRunning() {
  // Đọc trạng thái an toàn
  lock_guard<mutex> lock(m_mutex);
  return m_isRunning;
}

void ModbusReaderApp::pollCommand(int timeout_ms) {
  // Luồng chính gọi API ZMQClient::pollForSignal
  string signal = m_zmqClient.pollForSignal(timeout_ms);
  if (!signal.empty()) {
    cout << "<< [CMD] Nhan lenh: " << signal << endl;
    if (signal == "STOP_CLIENT") {
      stop();  // Gọi hàm stop an toàn
    }
  }
}

// --- LOGIC LUỒNG PHỤ (SENDER THREAD ROUTINE) ---
void ModbusReaderApp::senderRoutine() {
  auto last_send_time = chrono::system_clock::now();

  // Thử kết nối ZMQ ngay khi bắt đầu luồng
  bool is_zmq_connected = m_zmqClient.connectBroker();

  while (true) {
    // 1. Kiểm tra cờ dừng (Thread-safe check)
    {
      lock_guard<mutex> lock(m_mutex);
      if (m_stopFlag) break;
    }

    // 2. Logic Auto-Reconnect
    if (!is_zmq_connected) {
      is_zmq_connected = attemptReconnect();
      if (!is_zmq_connected) {
        continue;
      }
    }

    // 3. Gửi Data Định kỳ
    auto current_time = chrono::system_clock::now();
    if (chrono::duration_cast<chrono::milliseconds>(current_time -
                                                    last_send_time)
            .count() >= SEND_INTERVAL_MS) {
      // Đọc data từ ModbusMaster
      string data = readModbusData();

      // Gửi qua ZMQ
      if (m_zmqClient.sendMessage(data)) {
        cout << ">> [SENDER] Sent: " << data << endl;
      } else {
        cerr << "[SENDER] Loi gui ZMQ. Mat ket noi. Kich hoat Reconnect."
             << endl;
        is_zmq_connected = false;
      }
      last_send_time = current_time;
    }

    // Ngủ ngắn (10ms) để giảm tải CPU
    this_thread::sleep_for(chrono::milliseconds(10));
  }
  cout << "[SENDER] Thread da ket thuc." << endl;
}

// --- CÁC HÀM HỖ TRỢ (IMPLEMENTATION) ---
bool ModbusReaderApp::attemptReconnect() {
  cout << "[RECONNECT] Thu ket noi lai ZMQ sau " << RECONNECT_DELAY_S << "s..."
       << endl;
  this_thread::sleep_for(chrono::seconds(RECONNECT_DELAY_S));

  if (m_zmqClient.connectBroker()) {
    cout << "[RECONNECT] Thanh cong!" << endl;
    return true;
  }
  return false;
}

string ModbusReaderApp::readModbusData() {
  // Gọi API ModbusMaster
  return m_modbusMaster.dataString4TestDB();
}
