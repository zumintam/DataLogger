Đây là file `README.md` hoàn chỉnh cho dự án SolarBK DataLogger của bạn. Nó bao gồm mô tả, cấu trúc, hướng dẫn cài đặt môi trường, và cách vận hành hệ thống một cách chuyên nghiệp.

-----

# 🛰️ SolarBK DataLogger ZMQ System

## 📝 Mô Tả Dự Án

Dự án này là một hệ thống thu thập và xử lý dữ liệu từ xa (Data Logger) được thiết kế để đọc dữ liệu từ các thiết bị năng lượng mặt trời (như Inverter, Meter) thông qua giao thức **Modbus**.

Hệ thống sử dụng thư viện **ZeroMQ (ZMQ)** để thiết lập kênh giao tiếp hiệu quả và bất đồng bộ giữa các thành phần dịch vụ chạy trên nền tảng **Linux**.

### Chức năng chính:

  * **Thu thập dữ liệu:** Đọc các thanh ghi Modbus (Holding, Input) dựa trên các file mapping (ví dụ: `Grid-tie inverter (04).csv`).
  * **Truyền tin:** Sử dụng mô hình ZMQ Router/Dealer và Push/Pull để định tuyến dữ liệu và lệnh.
  * **Vận hành tự động:** Tích hợp **Systemd** để quản lý dịch vụ, đảm bảo hệ thống tự khởi động và tự khôi phục khi có lỗi.

-----

## ⚙️ Cấu Trúc Hệ Thống (ZMQ Topology)

Hệ thống được chia thành bốn thành phần chính giao tiếp qua các socket ZMQ khác nhau:

| Thành phần | Ngôn ngữ | Vai trò chính | Socket Type & Địa chỉ |
| :--- | :--- | :--- | :--- |
| **Modbus Reader** | C++ | Đọc Modbus và gửi/nhận lệnh. | DEALER `ipc://test.ipc` |
| **Broker** | Python | **Định tuyến** dữ liệu từ Reader đến Processor và lệnh từ Sender đến Reader. | ROUTER `ipc://test.ipc`, PULL `tcp://*:5556`, PUSH `ipc://data_stream.ipc` |
| **Processor** | Python | Nhận dữ liệu thô, xử lý và lưu trữ (DB/Cloud). | PULL `ipc://data_stream.ipc` |
| **Command Sender** | Python | Gửi lệnh điều khiển (ví dụ: Stop) tới Broker. | PUSH `tcp://*:5556` |

-----

## 🛠️ Yêu Cầu Hệ Thống

  * **Hệ điều hành:** Linux (Ưu tiên Ubuntu/Debian/Raspbian).
  * **Công cụ:** Git, CMake/Make (hoặc công cụ build C++ tương đương), Python 3.
  * **Thư viện:**
      * **C++:** Libmodbus, Libzmq.
      * **Python:** `pyzmq`.

## 🚀 Hướng Dẫn Cài Đặt và Khởi Động

Giả sử bạn đang làm việc trong thư mục gốc của dự án sau khi clone.

### 1\. Clone Project

```bash
git clone https://github.com/zumintam/DataLogger.git
cd DataLogger
```

### 2\. Cài đặt Môi Trường Python

Việc cài đặt môi trường ảo (`venv`) là **bắt buộc** để đảm bảo các tiến trình Python chạy đúng thư viện và không bị xung đột với hệ thống.

```bash
# 1. Cài đặt mô-đun venv nếu chưa có (trên Ubuntu/Debian)
sudo apt install python3-venv 

# 2. Tạo môi trường ảo
python3 -m venv venv

# 3. Cài đặt thư viện Python (pyzmq, ...)
source venv/bin/activate
pip install pyzmq # Hoặc pip install -r requirements.txt nếu có
deactivate
```

### 3\. Biên dịch Client C++

Bạn cần đảm bảo file thực thi `modbus_reader` đã được tạo và nằm trong thư mục gốc của dự án.

```bash
# (Ví dụ: Các bước build C++ của bạn, giả sử sử dụng Makefile)
# Ví dụ: make all
# Đảm bảo file './modbus_reader' đã tồn tại sau khi build
```

### 4\. Chuẩn bị Script Khởi động

Đảm bảo file run_all.sh đã được sửa để sử dụng đường dẫn tuyệt đối đến `venv/bin/python` và có quyền thực thi.

```bash
chmod +x run_all.sh
```

## 🏃 Vận Hành Hệ thống

### A. Khởi động Tự động (Production/Service)

Chạy script trực tiếp trong terminal để xem output ngay lập tức (sẽ block terminal):

```bash
./run_all.sh
```

Xem database 
sqlite3 data_log.db
sqlite> .tables
sqlite> SELECT * FROM <tên_bảng> ORDER BY timestamp DESC LIMIT 5;
sqlite> .quit


  * **Dừng:** Nhấn `Ctrl+C` để kích hoạt hàm `cleanup` và dừng tất cả tiến trình con một cách an toàn.

-----

## 🛑 Tắt Hệ Thống và Gỡ Lỗi

| Lệnh | Mô tả |
| :--- | :--- |
| `sudo systemctl stop datarunner.service` | **Tắt dịch vụ** nếu đang chạy bằng Systemd. |
| `ps aux | grep -i [b]roker` | Kiểm tra xem các tiến trình Python (Broker/Processor) còn chạy không. |
| `rm -f test.ipc data_stream.ipc` | **Dọn dẹp thủ công** các file socket IPC nếu có lỗi bind xảy ra (chỉ cần thiết nếu script không dọn dẹp). |
| `git status` | Kiểm tra xem có file nào chưa được commit hoặc push lên repository không. |