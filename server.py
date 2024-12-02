import socket
import sys
import time
import os
import struct

print("\nWelcome to the FTP server.\n\nTo get started, connect a client.")

# Thiết lập socket
TCP_IP = "192.168.1.19"  # Chỉ hoạt động cục bộ
TCP_PORT = 8080
       # Cổng TCP
BUFFER_SIZE = 1024    # Kích thước buffer
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()

print("\nConnected to by address: {}".format(addr))


def upld(conn):
    """Nhận file từ client"""
    try:
        # Gửi tín hiệu sẵn sàng nhận thông tin file
        conn.sendall(b"OK")  # Thay vì "1", dùng chuỗi byte rõ ràng

        # Nhận kích thước tên file và tên file
        file_name_size = struct.unpack("h", conn.recv(2))[0]
        file_name = conn.recv(file_name_size).decode()

        # Gửi tín hiệu sẵn sàng nhận kích thước file
        conn.sendall(b"OK")

        # Nhận kích thước file
        file_size = struct.unpack("i", conn.recv(4))[0]
        print(f"Receiving file: {file_name} (size: {file_size} bytes)")

        # Bắt đầu nhận dữ liệu file
        with open(file_name, "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                bytes_received += len(data)

        print(f"File {file_name} received successfully.")

        # Gửi lại thông tin hiệu suất upload
        conn.sendall(struct.pack("f", time.time()))
        conn.sendall(struct.pack("i", file_size))

    except Exception as e:
        print(f"Error in uploading file: {e}")
        conn.sendall(b"ERROR")  # Gửi tín hiệu lỗi tới client

def list_files():
    """Xử lý yêu cầu liệt kê file từ client."""
    print("Listing files...")
    listing = os.listdir(os.getcwd())
    conn.sendall(struct.pack("i", len(listing)))
    total_directory_size = 0

    for file_name in listing:
        file_name_encoded = file_name.encode()
        conn.sendall(struct.pack("i", len(file_name_encoded)))
        conn.sendall(file_name_encoded)
        file_size = os.path.getsize(file_name)
        conn.sendall(struct.pack("i", file_size))
        total_directory_size += file_size
        conn.recv(BUFFER_SIZE)  # Đồng bộ hóa với client

    conn.sendall(struct.pack("i", total_directory_size))
    conn.recv(BUFFER_SIZE)  # Đồng bộ hóa lần cuối
    print("Successfully sent file listing")


def dwld():
    """Xử lý yêu cầu tải file từ client."""
    conn.sendall(b"1")
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length).decode()

    if os.path.isfile(file_name):
        conn.sendall(struct.pack("i", os.path.getsize(file_name)))
    else:
        print("File not found: {}".format(file_name))
        conn.sendall(struct.pack("i", -1))
        return

    conn.recv(BUFFER_SIZE)  # Chờ tín hiệu tiếp tục từ client

    start_time = time.time()
    print("Sending file...")
    with open(file_name, "rb") as content:
        while True:
            data = content.read(BUFFER_SIZE)
            if not data:
                break
            conn.sendall(data)
    conn.recv(BUFFER_SIZE)  # Chờ tín hiệu đồng bộ từ client
    conn.sendall(struct.pack("f", time.time() - start_time))


def delf():
    """Xử lý yêu cầu xóa file từ client."""
    conn.sendall(b"1")
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length).decode()

    if os.path.isfile(file_name):
        conn.sendall(struct.pack("i", 1))
    else:
        conn.sendall(struct.pack("i", -1))
        return

    confirm_delete = conn.recv(BUFFER_SIZE).decode()
    if confirm_delete == "Y":
        try:
            os.remove(file_name)
            conn.sendall(struct.pack("i", 1))
            print("Deleted file: {}".format(file_name))
        except Exception as e:
            print("Error deleting file: {}".format(e))
            conn.sendall(struct.pack("i", -1))
    else:
        print("Delete operation aborted by client.")


def quit():
    """Xử lý yêu cầu thoát."""
    conn.sendall(b"1")
    conn.close()
    s.close()
    print("Server shut down.")
    sys.exit(0)


while True:
    print("\n\nWaiting for instruction...")
    data = conn.recv(BUFFER_SIZE).decode()
    print("\nReceived instruction: {}".format(data))

    if data == "UPLD":
        upld(conn)
    elif data == "LIST":
        list_files()
    elif data == "DWLD":
        dwld()
    elif data == "DELF":
        delf()
    elif data == "QUIT":
        quit()
    else:
        print("Unknown command received: {}".format(data))
