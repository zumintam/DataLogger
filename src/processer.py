# -*- coding: utf-8 -*-
import zmq
import time
import sys

# --- CẤU HÌNH ZMQ ---
# PHẢI TRÙNG VỚI địa chỉ PUSH của Broker (ipc://data_stream.ipc)
BROKER_DATA_STREAM = "ipc://data_stream.ipc"


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """
    Cố gắng giải mã bytes sang string (ưu tiên UTF-8).
    Nếu không thành công, trả về chuỗi hex của bytes đó.
    """
    try:
        # Cố gắng decode
        return data.decode(encoding)
    except UnicodeDecodeError:
        # Trả về hex nếu decode thất bại
        return data.hex()


def run_processer():
    # Sử dụng 'with' statement để đảm bảo cleanup Context
    with zmq.Context() as context:

        # PULL socket - Nhận dữ liệu theo luồng từ PUSH của Broker
        processer = context.socket(zmq.PULL)

        try:
            processer.connect(BROKER_DATA_STREAM)
            print(f"[PROCESSER] Đã kết nối tới Broker tại {BROKER_DATA_STREAM}")
            print("-------------------------------------------------------")
            print("Processer đang chờ dữ liệu...")

            # --- Vòng lặp chính ---
            while True:
                # Nhận tin nhắn đa phần (Multipart Message).
                # Luôn mong đợi 2 frames: [CLIENT_ID] và [DATA]
                message = processer.recv_multipart()

                if len(message) == 2:
                    client_id_bytes = message[0]
                    data_payload = message[1]

                    # Giải mã dữ liệu nhận được bằng hàm an toàn
                    client_id_display = safe_decode(client_id_bytes)
                    data_display = safe_decode(data_payload)

                    print(f"--- Bắt đầu Xử Lý ---")
                    print(f"[RECV DATA] Từ ID: {client_id_display}")
                    print(f"[PROCESS] Dữ liệu: {data_display}")

                    # Giả lập thời gian xử lý
                    time.sleep(0.3)
                    print("[PROCESS] Xử lý hoàn tất.")
                    print("-------------------------")
                else:
                    # Bỏ qua các tin nhắn không đúng định dạng 2-frame
                    print(
                        f"[WARN] Tin nhắn không hợp lệ ({len(message)} frames). Bỏ qua."
                    )

        except KeyboardInterrupt:
            print("\n[PROCESSER] Đã nhận tín hiệu dừng (Ctrl+C). Đang thoát.")
        except zmq.error.ContextTerminated:
            print("\n[PROCESSER] Context ZeroMQ đã bị chấm dứt.")
        except Exception as e:
            print(f"[FATAL] Lỗi không mong muốn: {e}")
        finally:
            print("\n[CLEANUP] Đang đóng socket...")
            processer.close()
            print("Processer đã dừng.")


if __name__ == "__main__":
    run_processer()
