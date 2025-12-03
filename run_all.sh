#!/bin/bash

# --- File script để khởi động toàn bộ hệ thống ZeroMQ (Broker, Client, Processer, Sender) ---

# Lấy đường dẫn tuyệt đối của thư mục gốc dự án, bất kể script được gọi từ đâu
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Nếu script nằm ở thư mục gốc, PROJECT_ROOT sẽ là SCRIPT_DIR
if [ "$PROJECT_ROOT" == "" ] || [ ! -d "$PROJECT_ROOT/venv" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"
fi

# Chuyển đến thư mục gốc để đảm bảo các lệnh sau chạy đúng
cd "$PROJECT_ROOT"

# Hàm để xử lý tín hiệu thoát (Ctrl+C)
cleanup() {
    echo ""
    echo "--- ĐÃ NHẬN TÍN HIỆU DỪNG (Ctrl+C) ---"
    
    # 1. Dừng các tiến trình Python (Broker, Processer, Sender)
    echo "Đang tìm và dừng tiến trình Broker (PID: $BROKER_PID)..."
    kill $BROKER_PID 2>/dev/null
    
    echo "Đang tìm và dừng tiến trình Processer (PID: $PROCESSER_PID)..."
    kill $PROCESSER_PID 2>/dev/null

    echo "Đang tìm và dừng tiến trình Command Sender (PID: $SENDER_PID)..."
    kill $SENDER_PID 2>/dev/null
    
    # 2. Dừng tiến trình C++ Client
    echo "Đang tìm và dừng tiến trình Modbus Reader (PID: $READER_PID)..."
    kill $READER_PID 2>/dev/null

    echo "Tất cả các tiến trình đã được dừng."
    exit 0
}

# Đăng ký hàm cleanup để chạy khi nhận tín hiệu SIGINT (Ctrl+C)
trap cleanup SIGINT

# 1. Kích hoạt môi trường ảo Python (Giả sử thư mục là 'venv')
echo "1. Kích hoạt môi trường ảo venv..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "[LỖI] Không thể kích hoạt venv. Đảm bảo bạn đã chạy: python3 -m venv venv"
    exit 1
fi

# 2. Chạy Broker ZeroMQ (Python) trong nền
echo "2. Khởi động Broker ZeroMQ (broker.py) trong nền..."
python src/broker.py &
BROKER_PID=$!
echo "   [INFO] Broker đã khởi động. PID: $BROKER_PID"

# Cho Broker một thời gian ngắn để bind TẤT CẢ socket (0.5 giây)
sleep 0.5 

# 3. Chạy Data Processer (Python) trong nền
echo "3. Khởi động Data Processer (processer.py) trong nền..."
python src/dataLogger.py &
PROCESSER_PID=$!
echo "   [INFO] Processer đã khởi động. PID: $PROCESSER_PID"


# # 4. Chạy Command Sender (Python Loop) trong nền
# echo "4. Khởi động Command Sender Loop (command_sender.py) trong nền..."
# python src/command_sender.py &
# SENDER_PID=$!
# echo "   [INFO] Sender đã khởi động. PID: $SENDER_PID"

# 5. Chạy Modbus Reader (C++) trong nền
echo "5. Khởi động Modbus Reader (./modbus_reader) trong nền..."
./modbus_reader &
READER_PID=$!
echo "   [INFO] Reader đã khởi động. PID: $READER_PID"

echo "--------------------------------------------------------"
echo "--- HỆ THỐNG ĐÃ SẴN SÀNG. NHẤN CTRL+C ĐỂ DỪNG ---"
echo "--------------------------------------------------------"

# 6. Giữ script chạy. Wait cho đến khi các tiến trình nền bị kill
wait