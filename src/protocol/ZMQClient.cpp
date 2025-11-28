#include "zeroMQ/ZMQClient.h"

#include <iostream>
#include <vector>

using namespace std;
ZMQClient::ZMQClient(const std::string& brokerAddress,
                     const std::string& clientID)
    : context_(1),
      socket_(context_, ZMQ_DEALER),
      brokerAddress_(brokerAddress),
      m_clientID(clientID)  // Lưu ID vào thành viên lớp
{
  // BẮT BUỘC: Thiết lập ZMQ_IDENTITY cho socket DEALER
  try {
    socket_.setsockopt(ZMQ_IDENTITY, m_clientID.data(), m_clientID.size());
    std::cout << "[ZMQ] Client ID set to: " << m_clientID << std::endl;
  } catch (const zmq::error_t& e) {
    std::cerr << "[ZMQ] ERROR: Khong the thiet lap ZMQ_IDENTITY: " << e.what()
              << std::endl;
  }
}

ZMQClient::~ZMQClient() {
  socket_.close();
  // context_.close() khong can thiet trong C++, context_ se bi huy tu dong
}

bool ZMQClient::connectBroker() {
  try {
    std::cout << "ZMQ Client dang ket noi den Broker tai " << brokerAddress_
              << std::endl;
    socket_.connect(brokerAddress_);
    std::cout << "Ket noi thanh cong." << std::endl;
    return true;
  } catch (const zmq::error_t& e) {
    std::cerr << "Loi ket noi ZMQ: " << e.what() << std::endl;
    return false;
  }
}

bool ZMQClient::sendMessage(const std::string& message) {
  try {
    zmq::message_t msg(message.size());
    memcpy(msg.data(), message.data(), message.size());

    socket_.send(msg, zmq::send_flags::none);
    return true;
  } catch (const zmq::error_t& e) {
    std::cerr << "Loi gui tin nhan ZMQ: " << e.what() << std::endl;
    return false;
  }
}

std::string ZMQClient::pollForSignal(long timeout_ms) {
  zmq::pollitem_t items[] = {{(void*)socket_, 0, ZMQ_POLLIN, 0}};

  // Polling de lang nghe tin nhan den
  zmq::poll(items, 1, timeout_ms);

  if (items[0].revents & ZMQ_POLLIN) {
    // Nhan tin nhan multipart (ID nguoi gui + delimiter + noi dung...)
    std::vector<zmq::message_t> parts;
    zmq::message_t part;

    while (socket_.recv(part, zmq::recv_flags::dontwait)) {
      parts.push_back(std::move(part));
      if (!socket_.get(zmq::sockopt::rcvmore)) break;
      part = zmq::message_t();
    }

    // Vi ta chi quan tam den noi dung tin hieu (frame cuoi cung)
    if (!parts.empty()) {
      return std::string(static_cast<char*>(parts.back().data()),
                         parts.back().size());
    }
  }
  return "";  // Khong co tin hieu nao
}