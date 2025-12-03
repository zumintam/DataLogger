# 🛰️ SolarBK DataLogger ZMQ System

## 📝 Mô Tả Dự Án
Hệ thống **SolarBK DataLogger** là giải pháp thu thập và xử lý dữ liệu từ các thiết bị năng lượng mặt trời (Inverter, Meter) thông qua giao thức Modbus. Hệ thống sử dụng **ZeroMQ (ZMQ)** để thiết lập kênh giao tiếp bất đồng bộ, hiệu quả cao giữa các dịch vụ chạy trên nền tảng Linux.

### Chức năng chính:
* **Thu thập dữ liệu:** Đọc các thanh ghi Modbus (Holding, Input) dựa trên mapping từ các file CSV.
* **Truyền tin:** Sử dụng mô hình ZMQ Router/Dealer và Push/Pull để định tuyến dữ liệu và lệnh điều khiển.
* **Vận hành tự động:** Tích hợp **Systemd** để quản lý dịch vụ, tự động khởi động khi boot và khôi phục (restart) khi gặp lỗi.

---

## ⚙️ Cấu Trúc Hệ Thống (ZMQ Topology)

### Sơ đồ luồng dữ liệu
```mermaid
graph TD
    CS[Command Sender] -- PUSH (tcp://*:5556) --> BR(Broker)
    MR[Modbus Reader] <-- DEALER/ROUTER (ipc://test.ipc) --> BR
    BR -- PUSH (ipc://data_stream.ipc) --> PR[Processor]
    
    style BR fill:#f9f,stroke:#333,stroke-width:2px
    style MR fill:#ccf,stroke:#333
    style PR fill:#cfc,stroke:#333