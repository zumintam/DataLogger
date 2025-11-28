#pragma once

#include <functional>
#include <string>
#include <zmq.hpp>

/**
 * @brief Class de quan ly socket ZMQ DEALER Client (Gui va Nhan)
 */
class ZMQClient {
 public:
  // Ham tao: Thiet lap dia chi Broker va ID Client
  ZMQClient(const std::string& brokerAddress, const std::string& clientID);

  // Ham huy: Dong socket va huy context ZMQ
  ~ZMQClient();

  // Ham ket noi den Broker
  bool connectBroker();

  // Ham gui tin nhan (data Modbus thô)
  bool sendMessage(const std::string& message);

  // Ham lang nghe tin hieu (vi du: lenh 'STOP' tu Python)

  std::string pollForSignal(long timeout_ms = 100);

 private:
  std::string m_clientID;  // Thêm biến lưu ID client
  zmq::context_t context_;
  zmq::socket_t socket_;
  std::string brokerAddress_;
};