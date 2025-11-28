# TÊN DỰ ÁN: Modbus ZeroMQ Reader
# MỤC TIÊU: Biên dịch các file .cpp thành file thực thi modbus_reader

# ----------------------------------------------------------------------
# 1. CẤU HÌNH BIẾN CHÍNH
# ----------------------------------------------------------------------
CXX := g++
TARGET := modbus_reader
BUILD_DIR := build

# Thư mục chứa tất cả các file nguồn .cpp
SRC_DIRS := src src/modbusStack src/protocol src/ModbusReaderApp

# Định nghĩa VPATH (đường dẫn tìm kiếm file nguồn cho quy tắc biên dịch)
VPATH := $(SRC_DIRS)

# ----------------------------------------------------------------------
# 2. KHAI BÁO CỜ BIÊN DỊCH VÀ LIÊN KẾT
# ----------------------------------------------------------------------
# CXXFLAGS: Cờ biên dịch
# -Iinclude: Thêm thư mục 'include' vào đường dẫn tìm kiếm header
# -std=c++17: Sử dụng chuẩn C++17
# -Wall: Bật tất cả các cảnh báo
# -pthread: Hỗ trợ đa luồng (cho C++)
CXXFLAGS := -Iinclude -std=c++17 -Wall -pthread

# LDFLAGS: Cờ liên kết
# -lzmq: Liên kết với thư viện ZeroMQ
# -lmodbus: Liên kết với thư viện libmodbus
LDFLAGS := -lzmq -lmodbus -pthread

# ----------------------------------------------------------------------
# 3. TẠO DANH SÁCH FILE
# ----------------------------------------------------------------------
# SRCS: Tìm kiếm tất cả các file .cpp trong các thư mục đã khai báo
SRCS := $(foreach dir, $(SRC_DIRS), $(wildcard $(dir)/*.cpp))

# OBJS: Tạo danh sách các file đối tượng .o, đặt trong thư mục build/
# Chỉ giữ lại tên file, không giữ đường dẫn thư mục gốc.
FILES_NO_DIR := $(notdir $(SRCS))
OBJS := $(patsubst %.cpp, $(BUILD_DIR)/%.o, $(FILES_NO_DIR))


# ----------------------------------------------------------------------
# 4. KHAI BÁO CÁC MỤC TIÊU ẢO (PHONY TARGETS)
# ----------------------------------------------------------------------
.PHONY: all clean mkdir

# ----------------------------------------------------------------------
# 5. QUY TẮC CHÍNH (DEFAULT TARGET)
# ----------------------------------------------------------------------
all: mkdir $(TARGET)

# Quy tắc tạo thư mục build
mkdir:
	@mkdir -p $(BUILD_DIR)

# ----------------------------------------------------------------------
# 6. QUY TẮC LIÊN KẾT (LINKING RULE)
# ----------------------------------------------------------------------
$(TARGET): $(OBJS)
	@echo "--- Lien ket cac file doi tuong ---"
	$(CXX) $^ -o $@ $(LDFLAGS)
	@echo "--- BUILD THANH CONG: $(TARGET) da duoc tao ---"

# ----------------------------------------------------------------------
# 7. QUY TẮC BIÊN DỊCH FILE (COMPILATION RULE)
# ----------------------------------------------------------------------
# Khi Makefile cần tạo build/file.o, nó sẽ tìm file.cpp trong các thư mục VPATH.
$(BUILD_DIR)/%.o: %.cpp
	@echo "Bien dich: $< (Tim thay trong VPATH)"
	$(CXX) $(CXXFLAGS) -c $< -o $@

# ----------------------------------------------------------------------
# 8. QUY TẮC DỌN DẸP
# ----------------------------------------------------------------------
clean:
	@echo "--- Don dep file build ---"
	@rm -rf $(BUILD_DIR) $(TARGET)