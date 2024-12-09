import socket
import sys
import time
import os
import struct
import threading
import datetime

print("\nWelcome to the FTP server.\n\nTo get started, connect a client.")

# Thiết lập socket  # Chỉ hoạt động cục bộ
# IP = socket.gethostbyname(socket.gethostname())
IP = "127.0.0.1"
PORT = 8080  # Cổng TCP
BUFFER_SIZE = 1024  # Kích thước buffer
FORMAT = "utf-8"



# Function to handle file upload
def upld(conn):
    """Nhận file từ client"""
    try:
        # Gửi tín hiệu sẵn sàng nhận thông tin file
        conn.sendall(b"OK")  # Thay vì "1", dùng chuỗi byte rõ ràng
        byte_recv = 0 
        # Nhận kích thước tên file và tên file
        file_name_size = struct.unpack("h", conn.recv(2))[0]
        
        conn.send(b"ok")

        file_name = conn.recv(file_name_size).decode()
        #chuan hoa ten file
        if os.path.isfile(file_name):
            # split ra 2 phan co dau cham . 
            nowTime = datetime.datetime.now()
            split_name = file_name.rsplit(".",1)
            file_name = ""
            file_name = f"{split_name[0]}({nowTime.day}-{nowTime.month}-{nowTime.year} {nowTime.hour}-{nowTime.minute}-{nowTime.second}).{split_name[1]}"
            print(file_name)
        # Gửi tín hiệu sẵn sàng nhận kích thước file
        conn.sendall(b"OK")

        # Nhận kích thước file
        file_size = struct.unpack("i", conn.recv(4))[0]
        print(f"Receiving file: {file_name} (size: {file_size} bytes)")
        conn.send(b"ok")
        # Bắt đầu nhận dữ liệu file
        bytes_received = 0
        with open(file_name, "wb") as f:
            while bytes_received < file_size:
                data = conn.recv(BUFFER_SIZE)
                if not data or data == b"ERROR":
                    break
                f.write(data)
                bytes_received += len(data)
        #thong bao ket thuc viec nhan file
        conn.send(b"Done")
        
        if data == b"ERROR":
            print("An error occurred on the client side when upload.")
        if(bytes_received == file_size):
            print(f"File {file_name} received successfully.")
            conn.send("FULL".encode(FORMAT))
        else:
            print(f"Somthinge is missing")
            conn.send("MISS".encode(FORMAT))
        # Gửi lại thông tin hiệu suất upload

    except Exception as e:
        print(f"Error in uploading file: {e}")
        conn.sendall(b"ERROR")  # Gửi tín hiệu lỗi tới client

# Function to list files
def list_files(conn):
    """Xử lý yêu cầu liệt kê file từ client."""
    print("Listing files...")
    try:
        # listing = []
        listing = os.listdir(os.getcwd())
        conn.sendall(struct.pack("!i", len(listing)))
        total_directory_size = 0

        for file_name in listing:
            file_name_encoded = file_name.encode()
            conn.sendall(struct.pack("i", len(file_name_encoded)))

            conn.recv(5)

            conn.sendall(file_name_encoded)
            conn.recv(5)
            
            file_size = os.path.getsize(file_name)
            conn.sendall(struct.pack("i", file_size))
            total_directory_size += file_size
            conn.recv(BUFFER_SIZE)  # Đồng bộ hóa với client

        conn.sendall(struct.pack("i", total_directory_size))
        conn.recv(BUFFER_SIZE)  # Đồng bộ hóa lần cuối
        print("Successfully sent file listing")
    except Exception as e:
        print(f"Error in listing files: {e}")
        conn.sendall(b"ERROR")

# Function to download a file
# Function to download a file
def dwld(conn):
    """Xử lý yêu cầu tải file từ client."""
    try:
        # Gửi tín hiệu sẵn sàng tải file
        conn.sendall(b"ok")

        # Nhận độ dài tên file và tên file từ client
        # file_name_length = struct.unpack("h", recv_all(conn, 2))[0]  # 2 bytes for the length
        file_name = conn.recv(BUFFER_SIZE).decode(FORMAT)
        #TODO
        # Kiểm tra sự tồn tại của file trên server
        if os.path.isfile(file_name):
            # Gửi kích thước của file nếu tồn tại
            # ! is big endian byte order gui byte quan trong nhat dau tien
            file_size = os.path.getsize(file_name) 
            packed_size = struct.pack('!i', file_size)
            conn.sendall(packed_size)
        else:
            # Nếu file không tồn tại, gửi -1 và thoát
            print(f"File {file_name} not found on server.")
            conn.sendall(struct.pack("!i", -1))
            return
        # Đợi tín hiệu tiếp theo từ client
        conn.recv(BUFFER_SIZE)
        # Gửi file tới client
        print(f"Sending file: {file_name}...")

        with open(file_name, "rb") as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                conn.sendall(data)

        # Chờ client đồng bộ và gửi thời gian đã dùng để tải file
        msg = conn.recv(BUFFER_SIZE)
        if(msg == b"ERROR"):
            print("An error occurred on the client side when download.")
    except ConnectionResetError as e :
        print(f"Connection was forcibly closed by the client: {e}")
        conn.sendall(b"ERROR")  # Gửi thông báo lỗi khi kết nối bị ngắt
    except Exception as e:
        print(f"Error in downloading file: {e}")
        conn.sendall(b"ERROR")  # Gửi thông báo lỗi chung nếu có lỗi khác

# Helper function to ensure that the correct number of bytes are received
def recv_all(conn, size):
    """Helper function to receive exactly 'size' bytes of data"""
    data = b""
    while len(data) < size:
        more_data = conn.recv(size - len(data))
        if not more_data:
            raise Exception("Connection closed unexpectedly.")
        data += more_data
    return data

# def upld_folder(conn):
    
# Function to delete a file
def delf(conn):
    """Xử lý yêu cầu xóa file từ client."""
    try:
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
                print(f"Deleted file: {file_name}")
            except Exception as e:
                print(f"Error deleting file: {e}")
                conn.sendall(struct.pack("i", -1))
        else:
            print("Delete operation aborted by client.")
    except Exception as e:
        print(f"Error in delete operation: {e}")
        conn.sendall(b"ERROR")

# Function to quit the server
def quit_server(conn):
    """Xử lý yêu cầu thoát."""
    try:
        conn.sendall(b"1")
        conn.close()
        print("Client disconnected.")
    except Exception as e:
        print(f"Error in quitting server: {e}")

# Function to handle each client connection in a separate thread
def handle_client(conn, addr):
    print(f"Handling new client: {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)

            # Kiểm tra nếu dữ liệu nhận về không rỗng
            if not data:
                print(f"Client {addr} disconnected.")
                break  # Hoặc thực hiện các biện pháp xử lý khác

            # Nếu có dữ liệu, thực hiện giải mã
            data = data.decode()

            print(f"Received instruction: {data}")

            if data == "UPLD":
                upld(conn)
            elif data == "LIST":
                list_files(conn)
            elif data == "DWLD":
                dwld(conn)
            elif data == "DELF":
                delf(conn)
            elif data == "QUIT":
                quit_server(conn)
                break
            else:
                print(f"Unknown command received: {data}")
                conn.sendall(b"ERROR")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

# Server main loop

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP, PORT))
    s.listen()  # Lắng nghe tối đa 5 kết nối
    print(f"[LISTEN] Server is listening on {IP}:{PORT}")
    while True:
        conn, addr = s.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()
        print(f"[Active connection] {threading.active_count() - 1} \n")

if __name__ == "__main__":
    main()
