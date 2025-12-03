import zmq
import time
import sqlite3
import re
from datetime import datetime
import sys

# --- CẤU HÌNH ZMQ ---
# PHẢI TRÙNG VỚI địa chỉ PUSH của Broker
BROKER_DATA_STREAM = "ipc://data_stream.ipc"

# --- CẤU HÌNH DATABASE ---
DB_FILE = "data_log.db"


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """Cố gắng giải mã bytes sang string (ưu tiên UTF-8), nếu thất bại trả về hex."""
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        return data.hex()


# =================================================================
# === HÀM XỬ LÝ DATABASE VÀ PHÂN TÍCH DATA ===
# =================================================================


def initialize_db(db_conn):
    """Tạo bảng cơ sở dữ liệu nếu chưa tồn tại."""
    cursor = db_conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            client_id TEXT NOT NULL,
            data_key TEXT NOT NULL,
            data_value REAL
        )
    """
    )
    db_conn.commit()
    print(f"[DB] Database '{DB_FILE}' đã sẵn sàng.")


def parse_data(data_string: str) -> dict:
    """
    Phân tích chuỗi dữ liệu Modbus (Ví dụ: 'timestamp=...; voltage=...; power=...;').
    Trả về một dictionary các cặp key-value.
    """
    parsed_data = {}

    # 1. Tách chuỗi bằng dấu chấm phẩy (;). Lọc bỏ các phần tử trống (do dấu ; ở cuối).
    parts = [p.strip() for p in data_string.split(";") if p.strip()]

    for part in parts:
        # 2. Tách từng cặp key=value bằng dấu bằng (=)
        if "=" in part:
            try:
                key, value_str = part.split("=", 1)
                key = key.strip()
                value_str = value_str.strip()

                # 3. Cố gắng chuyển đổi thành số thực (REAL)
                try:
                    # Nếu là số, lưu dưới dạng float
                    numeric_value = float(value_str)
                    parsed_data[key] = numeric_value
                except ValueError:
                    # Nếu không phải số (ví dụ: timestamp), lưu dưới dạng chuỗi
                    parsed_data[key] = value_str
            except Exception:
                # Bỏ qua nếu có lỗi phân tích cú pháp bất thường
                pass
    return parsed_data


def insert_data(db_conn, client_id: str, data: dict):
    """
    Chèn từng cặp key-value đã phân tích vào bảng sensor_data,
    sử dụng timestamp từ dữ liệu Modbus cho cột DATETIME.
    Chỉ chèn các giá trị là số (REAL).
    """

    # Lấy timestamp từ dữ liệu, mặc định là thời gian hiện tại nếu không có
    modbus_timestamp = data.get(
        "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Nếu timestamp trong data là số (do parse_data) hoặc không phải chuỗi, sử dụng thời gian hiện tại
    if not isinstance(modbus_timestamp, str):
        modbus_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Đếm số lượng bản ghi mới
    new_records = 0
    cursor = db_conn.cursor()

    # Duyệt qua từng cặp (key, value)
    for key, value in data.items():
        # Bỏ qua trường 'timestamp' vì nó đã được xử lý
        if key == "timestamp":
            continue

        # Chỉ chèn dữ liệu số (REAL) vì cột data_value là REAL
        if isinstance(value, (int, float)):
            cursor.execute(
                """
                INSERT INTO sensor_data (timestamp, client_id, data_key, data_value)
                VALUES (?, ?, ?, ?)
            """,
                (modbus_timestamp, client_id, key, value),
            )
            new_records += 1

    db_conn.commit()
    print(f"      [DB LOG] Đã ghi {new_records} trường dữ liệu vào DB.")


# =================================================================
# === LUỒNG ZERO MQ CHÍNH (PULL) ===
# =================================================================


def run_data_logger():
    context = zmq.Context()
    conn = None  # Biến kết nối DB

    try:
        # 1. Khởi tạo Database
        # Đây là nơi lỗi 'database disk image is malformed' xảy ra nếu file bị hỏng
        conn = sqlite3.connect(DB_FILE)
        initialize_db(conn)

        # 2. Khởi tạo Socket ZMQ
        data_logger = context.socket(zmq.PULL)
        data_logger.connect(BROKER_DATA_STREAM)
        print(f"[DATA LOGGER] Đã kết nối tới Broker tại {BROKER_DATA_STREAM}")
        print("-------------------------------------------------------")
        print("Data Logger đang chờ dữ liệu...")

        default_client_id = "UNKNOWN_ID"

        while True:
            # Nhận tin nhắn đa phần
            message = data_logger.recv_multipart()

            client_id_display = default_client_id
            data_payload = None

            if len(message) == 2:
                # Trường hợp 1: Nhận đủ 2 frame (ID + DATA)
                client_id_bytes = message[0]
                data_payload = message[1]
                client_id_display = safe_decode(client_id_bytes)

            elif len(message) == 1:
                # Trường hợp 2: Broker chỉ gửi Data (1 frame)
                data_payload = message[0]
                client_id_display = default_client_id

            if data_payload:
                # Giải mã chuỗi dữ liệu
                data_string = safe_decode(data_payload)

                print(f"--- Bắt đầu Ghi Log ---")
                print(f"[RECV DATA] Từ ID: {client_id_display}")
                print(f"[PROCESS] Chuỗi Dữ liệu: {data_string}")

                # Phân tích và ghi vào DB
                parsed_data = parse_data(data_string)
                if parsed_data:
                    insert_data(conn, client_id_display, parsed_data)
                else:
                    print("[WARN] Không phân tích được cặp key-value nào.")

                print("[PROCESS] Xử lý hoàn tất.")
                print("-------------------------")
            else:
                print(
                    f"[WARN] Tin nhắn không hợp lệ ({len(message)} frames): {message}"
                )

    except KeyboardInterrupt:
        print("\n[LOGGER] Đã nhận tín hiệu dừng (Ctrl+C). Đang thoát.")
    except zmq.error.ContextTerminated:
        print("\n[LOGGER] Context ZeroMQ đã bị chấm dứt.")
    except Exception as e:
        # Lỗi FATAL thường là database disk image is malformed
        print(f"[FATAL] Lỗi không mong muốn: {e}")
    finally:
        if "data_logger" in locals() and not data_logger.closed:
            data_logger.close()
        if conn:
            conn.close()
            print("[DB] Đã đóng kết nối database.")
        context.term()
        print("Data Logger đã dừng.")


if __name__ == "__main__":
    run_data_logger()
