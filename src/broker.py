import zmq
import time
import sys

# --- CAU HINH DIA CHI ZMQ ---
FRONTEND_ADDR = "ipc://test.ipc"  # ROUTER nhận từ Modbus Reader
COMMAND_ADDR = "ipc://command.ipc"  # PULL nhận lệnh điều khiển
BROKER_DATA_STREAM = "ipc://data_stream.ipc"  # PUSH gửi dữ liệu tới Processer (ĐÃ THÊM)

# --- CAU HINH ID ---
# Đảm bảo TARGET_CLIENT_ID là bytes và khớp với ID mà Client (C++) gửi đi
TARGET_CLIENT_ID = b"ModbusReader_01"


def safe_decode(data: bytes) -> str:
    """Cố gắng giải mã bytes sang string (ưu tiên UTF-8), nếu thất bại trả về hex."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.hex()


def run_broker():
    # Sử dụng 'with' statement để đảm bảo cleanup
    with zmq.Context() as context:

        # 1. Socket Giao tiếp hai chiều với Client
        frontend = context.socket(zmq.ROUTER)
        # 2. Socket Nhận Lệnh điều khiển
        command_in = context.socket(zmq.PULL)
        # 3. Socket Gửi Dữ liệu tới Processer
        data_out = context.socket(zmq.PUSH)  # <--- ĐÃ KHAI BÁO

        try:
            # Gan (Bind) cac Socket
            frontend.bind(FRONTEND_ADDR)
            print(f"[BROKER] ROUTER listening at {FRONTEND_ADDR}")

            command_in.bind(COMMAND_ADDR)
            print(f"[BROKER] PULL listening at {COMMAND_ADDR}")

            data_out.bind(BROKER_DATA_STREAM)  # <--- BIND SOCKET PUSH
            print(f"[BROKER] PUSH data stream bound at {BROKER_DATA_STREAM}")

            # Khai báo Poller
            poller = zmq.Poller()
            poller.register(frontend, zmq.POLLIN)
            poller.register(command_in, zmq.POLLIN)

            print("-------------------------------------------------------")
            print("Broker đang chạy...")

            while True:
                socks = dict(poller.poll(100))

                # --- 1. XU LY DU LIEU TU MODBUS READER (ROUTER nhan) ---
                if frontend in socks and socks[frontend] & zmq.POLLIN:
                    try:
                        message = frontend.recv_multipart()

                        if len(message) == 2:
                            client_id_bytes = message[0]
                            data_payload = message[1]

                            client_id_display = safe_decode(client_id_bytes)
                            data_display = safe_decode(data_payload)

                            is_string = True
                            try:
                                data_payload.decode("utf-8")
                            except UnicodeDecodeError:
                                is_string = False
                            display_format = "String" if is_string else "Hex"

                            print(
                                f"[RECV DATA] [ID: {client_id_display}] -> [Data {display_format}: {data_display}]"
                            )

                            # BƯỚC QUAN TRỌNG: CHUYỂN TIẾP ID VÀ DATA TỚI PROCESSER (2 frame)
                            data_out.send_multipart([client_id_bytes, data_payload])
                            print(
                                f"      [FORWARD] ID and Data forward to Processer ({len(data_payload)} bytes)."
                            )

                        else:
                            print(
                                f"[WARN] Frame không hợp lệ ({len(message)} frames):",
                                message,
                            )

                    except zmq.error.ZMQError as e:
                        print(f"[ERROR] Loi ZMQ khi nhan du lieu: {e}")

                # --- 2. XU LY LENH ĐIỀU KHIỂN (PULL nhan) ---
                if command_in in socks and socks[command_in] & zmq.POLLIN:
                    try:
                        command = command_in.recv_string()
                        print(f"[RECV CMD] '{command}'")

                        if command.upper() == "STOP_BROKER":
                            print("Đang dừng Broker...")
                            break

                        # Gửi lệnh tới CLIENT (DEALER) -> [TARGET_IDENTITY][EMPTY][DATA]
                        frontend.send_multipart(
                            [TARGET_CLIENT_ID, b"", command.encode("utf-8")]
                        )

                        target_id_display = TARGET_CLIENT_ID.decode(
                            "utf-8", errors="ignore"
                        )
                        print(f"[SEND CMD] '{command}' -> {target_id_display}")

                    except zmq.error.ZMQError as e:
                        print(f"[ERROR] Loi ZMQ khi nhan lenh: {e}")

        except Exception as e:
            print(f"\n[FATAL ERROR] Lỗi không mong muốn: {e}")
            sys.exit(1)

        finally:
            print("\n[CLEANUP] Đang đóng sockets...")
            frontend.close()
            command_in.close()
            data_out.close()  # <--- Đóng socket PUSH
            print("Broker đã dừng.")


if __name__ == "__main__":
    run_broker()
