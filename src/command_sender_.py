import zmq
import time

# Địa chỉ kết nối cho Processer (PULL) để nhận dữ liệu.
# Nó PHẢI TRÙNG VỚI DATA_STREAM_ADDR CỦA BROKER (thường là một socket PUSH).
BROKER_DATA_STREAM = "ipc://data_stream.ipc"


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """
    Cố gắng giải mã bytes sang string (ưu tiên UTF-8).
    Nếu không thành công (UnicodeDecodeError), trả về chuỗi hex của bytes đó.
    """
    try:
        # Cố gắng decode
        return data.decode(encoding)
    except UnicodeDecodeError:
        # Tra ve hex nếu decode thất bại, để đảm bảo luôn có kết quả hiển thị
        return data.hex()


def run_processer():
    context = zmq.Context()

    # 1. Khởi tạo socket ZMQ loại PULL.
    # Socket PULL được thiết kế để nhận dữ liệu từ các socket PUSH (từ Broker).
    processer = context.socket(zmq.PULL)

    # 2. Kết nối tới địa chỉ của Broker (socket PUSH).
    processer.connect(BROKER_DATA_STREAM)
    print(f"[PROCESSER] Đã kết nối tới Broker tại {BROKER_DATA_STREAM}")
    print("-------------------------------------------------------")
    print("Processer đang chờ dữ liệu...")

    while True:
        try:
            # 3. Nhận tin nhắn đa phần (Multipart Message).
            # Trong kiến trúc này, Broker (PUSH) gửi, Processer (PULL) nhận.
            # Tin nhắn mong đợi từ Broker: [CLIENT_ID] và [DATA_PAYLOAD]
            message = processer.recv_multipart()
        except zmq.error.ContextTerminated:
            # Xử lý khi ZMQ Context bị dừng (thường là khi Broker/Main Process bị tắt)
            print("[PROCESSER] Broker bị dừng, kết thúc.")
            break

        if len(message) == 2:
            # Trường hợp chuẩn: Nhận đủ 2 frame: ID và Data
            client_id_bytes = message[0]
            data_payload = message[1]

            # Giải mã dữ liệu nhận được bằng hàm an toàn để đảm bảo hiển thị
            client_id_display = safe_decode(client_id_bytes)
            data_display = safe_decode(data_payload)

            print(f"--- Bắt đầu Xử Lý ---")
            print(f"[RECV DATA] Từ ID: {client_id_display}")
            print(f"[PROCESS] Dữ liệu: {data_display}")

            # Giả lập thời gian xử lý thực tế của nghiệp vụ
            # time.sleep(0.3)
            print("[PROCESS] Xử lý hoàn tất.")
            print("-------------------------")
        elif len(message) == 1:
            # Xử lý trường hợp Broker chỉ gửi Data (1 frame) - nếu không dùng ID
            data_payload = message[0]
            data_display = safe_decode(data_payload)

            print(f"--- Bắt đầu Xử Lý ---")
            print(f"[RECV DATA] (Không có ID) - Dữ liệu: {data_display}")

            time.sleep(0.3)
            print("[PROCESS] Xử lý hoàn tất.")
            print("-------------------------")
        else:
            # Cảnh báo nếu nhận được số lượng frame không mong đợi
            print(f"[WARN] Tin nhắn không hợp lệ ({len(message)} frames): {message}")

    processer.close()
    context.term()
    print("Processer đã dừng.")


if __name__ == "__main__":
    run_processer()
