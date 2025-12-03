import zmq
import time

BROKER_DATA_STREAM = (
    "ipc://data_stream.ipc"  # PHẢI TRÙNG VỚI DATA_STREAM_ADDR CỦA BROKER
)


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """
    Cố gắng giải mã bytes sang string (ưu tiên UTF-8).
    Nếu không thành công, trả về chuỗi hex của bytes đó.
    """
    try:
        # Cố gắng decode
        return data.decode(encoding)
    except UnicodeDecodeError:
        # Tra ve hex nếu decode thất bại
        return data.hex()


def run_processer():
    context = zmq.Context()

    # PULL socket - Nhận dữ liệu từ PUSH của Broker
    processer = context.socket(zmq.PULL)
    processer.connect(BROKER_DATA_STREAM)
    print(f"[PROCESSER] Đã kết nối tới Broker tại {BROKER_DATA_STREAM}")
    print("-------------------------------------------------------")
    print("Processer đang chờ dữ liệu...")

    while True:
        try:
            # Nhận tin nhắn đa phần (Multipart Message).
            # Nếu Broker được sửa để gửi 2 frame, Processer sẽ nhận được: [CLIENT_ID] và [DATA]
            message = processer.recv_multipart()
        except zmq.error.ContextTerminated:
            print("[PROCESSER] Broker bị dừng, kết thúc.")
            break

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
        elif len(message) == 1:
            # Xử lý trường hợp Broker chỉ gửi Data (1 frame)
            data_payload = message[0]
            data_display = safe_decode(data_payload)

            print(f"--- Bắt đầu Xử Lý ---")
            print(f"[RECV DATA] (Không có ID) - Dữ liệu: {data_display}")

            time.sleep(0.3)
            print("[PROCESS] Xử lý hoàn tất.")
            print("-------------------------")
        else:
            print(f"[WARN] Tin nhắn không hợp lệ ({len(message)} frames): {message}")

    processer.close()
    context.term()
    print("Processer đã dừng.")


if __name__ == "__main__":
    run_processer()
