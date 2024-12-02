import socket
import sys
import os
import struct

# Khởi tạo thông tin kết nối
TCP_IP = "192.168.1.19"  # Server IP (local)
TCP_PORT = 8080
       # Server port
BUFFER_SIZE = 4096    # Kích thước buffer chuẩn
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def conn():
    """Kết nối đến server."""
    print("Sending server request...")
    try:
        s.connect((TCP_IP, TCP_PORT))
        print("Connection successful!")
    except Exception as e:
        print(f"Connection unsuccessful. Error: {e}")
        sys.exit()

def upld(s, file_name):
    """Upload file lên server"""
    try:
        # Kiểm tra file tồn tại
        if not os.path.isfile(file_name):
            print("File không tồn tại. Kiểm tra đường dẫn.")
            return

        # Lấy kích thước file
        file_size = os.path.getsize(file_name)
        print(f"Uploading file: {file_name} (size: {file_size} bytes)")

        # Gửi yêu cầu upload
        s.sendall(b"UPLD")

        # Đợi phản hồi từ server
        if s.recv(BUFFER_SIZE).decode() != "OK":
            print("Server không phản hồi. Hủy quá trình.")
            return

        # Gửi kích thước tên file và tên file
        file_name_encoded = file_name.encode()
        s.sendall(struct.pack("h", len(file_name_encoded)))
        s.sendall(file_name_encoded)

        # Đợi server xác nhận
        if s.recv(BUFFER_SIZE).decode() != "OK":
            print("Server không phản hồi. Hủy quá trình.")
            return

        # Gửi kích thước file
        s.sendall(struct.pack("i", file_size))

        # Gửi dữ liệu file
        with open(file_name, "rb") as f:
            print("Sending...")
            while chunk := f.read(BUFFER_SIZE):
                s.sendall(chunk)

        # Nhận thông tin hiệu suất từ server
        upload_time = struct.unpack("f", s.recv(4))[0]
        upload_size = struct.unpack("i", s.recv(4))[0]
        print(f"Upload completed. Time: {upload_time:.2f}s, Size: {upload_size} bytes")

    except Exception as e:
        print(f"Lỗi khi upload file: {e}")


def list_files():
    """Liệt kê các file trên server."""
    print("Requesting file list...\n")
    try:
        s.sendall(b"LIST")
        number_of_files = struct.unpack("i", s.recv(4))[0]
        for _ in range(number_of_files):
            file_name_size = struct.unpack("i", s.recv(4))[0]
            file_name = s.recv(file_name_size).decode()
            file_size = struct.unpack("i", s.recv(4))[0]
            print(f"\t{file_name} - {file_size} bytes")
            s.sendall(b"1")
        total_directory_size = struct.unpack("i", s.recv(4))[0]
        print(f"Total directory size: {total_directory_size} bytes")
        s.sendall(b"1")
    except Exception as e:
        print(f"Error listing files: {e}")

def dwld(file_name):
    """Download file từ server."""
    print(f"\nDownloading file: {file_name}")
    try:
        s.sendall(b"DWLD")
        s.recv(BUFFER_SIZE)
        s.sendall(struct.pack("h", len(file_name)))
        s.sendall(file_name.encode())
        file_size = struct.unpack("i", s.recv(4))[0]
        if file_size == -1:
            print("File does not exist.")
            return
        s.sendall(b"1")
        with open(file_name, "wb") as output_file:
            bytes_received = 0
            print("\nDownloading...")
            while bytes_received < file_size:
                data = s.recv(BUFFER_SIZE)
                output_file.write(data)
                bytes_received += len(data)
            print(f"Successfully downloaded {file_name}")
        time_elapsed = struct.unpack("f", s.recv(4))[0]
        print(f"Time elapsed: {time_elapsed:.2f}s\nFile size: {file_size} bytes")
    except Exception as e:
        print(f"Error downloading file: {e}")

def delf(file_name):
    """Xóa file trên server."""
    print(f"Deleting file: {file_name}...")
    try:
        s.sendall(b"DELF")
        s.recv(BUFFER_SIZE)
        s.sendall(struct.pack("h", len(file_name)))
        s.sendall(file_name.encode())
        file_exists = struct.unpack("i", s.recv(4))[0]
        if file_exists == -1:
            print("File does not exist.")
            return
        confirm = input(f"Are you sure you want to delete {file_name}? (Y/N): ").upper()
        if confirm in ["Y", "YES"]:
            s.sendall(b"Y")
            delete_status = struct.unpack("i", s.recv(4))[0]
            if delete_status == 1:
                print("File successfully deleted.")
            else:
                print("File deletion failed.")
        else:
            s.sendall(b"N")
            print("Deletion cancelled.")
    except Exception as e:
        print(f"Error deleting file: {e}")

def quit():
    """Ngắt kết nối."""
    try:
        s.sendall(b"QUIT")
        s.recv(BUFFER_SIZE)
        s.close()
        print("Disconnected from server.")
    except Exception as e:
        print(f"Error during disconnection: {e}")

# Menu điều khiển
print("\nWelcome to the FTP client.\n")
print("Available commands:")
print("CONN           : Connect to server")
print("UPLD file_path : Upload file")
print("LIST           : List files")
print("DWLD file_path : Download file")
print("DELF file_path : Delete file")
print("QUIT           : Exit")

while True:
    command = input("\nEnter a command: ").strip()
    if command[:4].upper() == "CONN":
        conn()
    elif command[:4].upper() == "UPLD":
        upld(s, command[5:].strip())
    elif command[:4].upper() == "LIST":
        list_files()
    elif command[:4].upper() == "DWLD":
        dwld(command[5:].strip())
    elif command[:4].upper() == "DELF":
        delf(command[5:].strip())
    elif command[:4].upper() == "QUIT":
        quit()
        break
    else:
        print("Command not recognised. Please try again.")
