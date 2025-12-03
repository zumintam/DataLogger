import zmq
import time
import sqlite3
import re
from datetime import datetime
import sys

# --- CẤU HÌNH ZMQ ---
BROKER_DATA_STREAM = "ipc://data_stream.ipc"

# --- CẤU HÌNH DATABASE ---
DB_FILE = "data_log.db"

# --- TAG CHUẨN (PHẢI TRÙNG C++ NẾU GỬI 3 FRAMES) ---
DATA_TYPE_ID_BYTES = b"DATA_SENSOR"


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        return data.hex()


# =================================================================
# === DATABASE =====================================================
# =================================================================


def initialize_db(db_conn):
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
    parsed_data = {}
    parts = data_string.split("|")

    for part in parts:
        if ":" in part:
            try:
                key, value_str = part.split(":", 1)
                key = key.strip()
                numeric_value_str = re.sub(r"[^0-9.\-]+", "", value_str)

                if numeric_value_str:
                    numeric_value = float(numeric_value_str)
                    parsed_data[key] = numeric_value
            except ValueError:
                pass
    return parsed_data


def insert_data(db_conn, client_id: str, data: dict):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db_conn.cursor()

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
# === ZERO MQ MAIN LOOP ============================================
# =================================================================


def run_data_logger():

    context = zmq.Context()
    conn = None

    try:
        # 1. Init DB
        conn = sqlite3.connect(DB_FILE)
        initialize_db(conn)

        # 2. ZMQ PULL
        data_logger = context.socket(zmq.PULL)
        data_logger.connect(BROKER_DATA_STREAM)
        print(f"[DATA LOGGER] Đã kết nối PUSH broker tại {BROKER_DATA_STREAM}")
        print("-------------------------------------------------------")
        print("Data Logger đang chờ dữ liệu...\n")

        while True:
            frames = data_logger.recv_multipart()
            frame_count = len(frames)

            print(
                f"\n[RAW FRAMES] {frame_count} frames: {[safe_decode(f) for f in frames]}"
            )

            # =====================================================================
            # AUTO-FIX: NHẬN 2 FRAMES —> CLIENT GỬI SAI CHUẨN => TỰ ĐIỀU CHỈNH
            # =====================================================================
            if frame_count == 2:
                f0, f1 = frames

                if f0 != DATA_TYPE_ID_BYTES:
                    print(
                        "[AUTO-FIX] Phát hiện client gửi 2 frames sai chuẩn => Tự suy ra:"
                    )
                    print("          - Frame 0 là ClientID")
                    print("          - Tự gán TAG = DATA_SENSOR")

                    client_id_display = safe_decode(f0)
                    data_tag = DATA_TYPE_ID_BYTES
                    data_payload = f1

                else:
                    # Trường hợp hiếm: frame[0] = TAG, frame[1] = PAYLOAD
                    print("[INFO] 2 frames nhưng hợp chuẩn TAG trước PAYLOAD.")
                    client_id_display = "UNKNOWN_ID"
                    data_tag = f0
                    data_payload = f1

            # =====================================================================
            # TRƯỜNG HỢP CHUẨN 3 FRAMES: ID + TAG + DATA
            # =====================================================================
            elif frame_count == 3:
                client_id_display = safe_decode(frames[0])
                data_tag = frames[1]
                data_payload = frames[2]

            else:
                print(f"[WARN] Frame count {frame_count} không hợp lệ! Bỏ qua.")
                continue

            # Kiểm tra TAG
            if data_tag != DATA_TYPE_ID_BYTES:
                print(f"[WARN] Sai TAG: {safe_decode(data_tag)}  (bỏ qua)")
                continue

            # Decode payload
            data_string = safe_decode(data_payload)

            print(f"[RECV DATA] ID = {client_id_display}")
            print(f"[DATA STR]  {data_string}")

            # Parse
            parsed_data = parse_data(data_string)
            if parsed_data:
                insert_data(conn, client_id_display, parsed_data)
            else:
                print("[WARN] Không phân tích được key-value.")

            print("[DONE] Xử lý xong.")
            print("------------------------------------")

    except KeyboardInterrupt:
        print("\n[LOGGER] Ctrl+C - Dừng lại.")

    except Exception as e:
        print(f"[FATAL] Lỗi: {e}")

    finally:
        if conn:
            conn.close()
            print("[DB] Đã đóng kết nối.")
        context.term()
        print("Data Logger đã dừng.")


# =====================================================================
# ENTRYPOINT
# =====================================================================

if __name__ == "__main__":
    run_data_logger()
