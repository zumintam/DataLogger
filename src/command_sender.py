import zmq
import time
import sqlite3
import re
from datetime import datetime
import sys

# --- CẤU HÌNH ZMQ ---
BROKER_DATA_STREAM = "ipc://data_stream.ipc"  # PHẢI TRÙNG VỚI địa chỉ PUSH của Broker

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
    Phân tích chuỗi dữ liệu Modbus (ví dụ: 'Pwr:450kW|Temp:35.21C').
    Trả về một dictionary các cặp key-value số thực.
    """
    parsed_data = {}

    # Tách chuỗi bằng dấu '|'
    parts = data_string.split("|")

    for part in parts:
        # Tách từng cặp key:value bằng dấu ':'
        if ":" in part:
            try:
                key, value_str = part.split(":", 1)
                key = key.strip()

                # Loại bỏ đơn vị (như 'kW', 'C') và chuyển đổi thành số thực (REAL)
                # Sử dụng regex để chỉ giữ lại số, dấu chấm và dấu trừ
                numeric_value_str = re.sub(r"[^0-9\.\-]+", "", value_str)

                if numeric_value_str:
                    numeric_value = float(numeric_value_str)
                    parsed_data[key] = numeric_value
            except ValueError:
                # Bỏ qua nếu giá trị không phải là số hợp lệ
                pass
    return parsed_data


def insert_data(db_conn, client_id: str, data: dict):
    """Chèn từng cặp key-value đã phân tích vào bảng sensor_data."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db_conn.cursor()

    # Duyệt qua từng cặp (key, value) đã được phân tích
    for key, value in data.items():
        cursor.execute(
            """
            INSERT INTO sensor_data (timestamp, client_id, data_key, data_value)
            VALUES (?, ?, ?, ?)
        """,
            (current_time, client_id, key, value),
        )

    db_conn.commit()
    print(f"      [DB LOG] Đã ghi {len(data)} trường dữ liệu vào DB.")


# =================================================================
# === LUỒNG ZERO MQ CHÍNH (PULL) ===
# =================================================================


def run_data_logger():
    context = zmq.Context()
    conn = None  # Biến kết nối DB

    try:
        # 1. Khởi tạo Database
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
