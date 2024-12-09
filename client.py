import socket
import os
import struct
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime # lay tg
import threading  # Import threading module


# Khởi tạo kết nối tới server
TCP_IP = "127.0.0.1"
TCP_PORT = 8080
BUFFER_SIZE = 1024
FORMAT ="utf-8"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# hàm ghi lại lịch sử connect
def history_conn(username, port):
    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_address = socket.gethostbyname(socket.gethostname())

    with open("LichSu_Login.txt", "a") as file:
        file.write(f"{thoi_gian} - Username: {username} - IP: {ip_address} - Port: {port}\n")

    print("Đã ghi lịch sử kết nối thành công.")
# Hàm kết nối đến server
def conn():
    try:
        s.connect((TCP_IP, TCP_PORT))
        messagebox.showinfo("Success", "Connected to the server.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to connect: {e}")

# Hàm tải lên file
def upld():
    #TODO lam 1 ham check loi
    file_path = filedialog.askopenfilename()
    if file_path:
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            s.sendall(b"UPLD")
            s.recv(BUFFER_SIZE)
            #send file_size name
            s.sendall(struct.pack("h", len(file_name)))
            s.recv(BUFFER_SIZE)
            # send file_name
            s.sendall(file_name.encode())
            s.recv(BUFFER_SIZE)
            #gui kich thuoc file
            s.sendall(struct.pack("i", file_size))
            s.recv(BUFFER_SIZE)
            # van chuyen du lieu
            with open(file_path, "rb") as f:
                # while (chunk := f.read(BUFFER_SIZE)):
                #     s.sendall(chunk)
                #     s.recv(BUFFER_SIZE)
                data = f.read(BUFFER_SIZE)
                while True:
                    s.sendall(data)
                    data = f.read(BUFFER_SIZE)
                    if not data :
                        break
            #nhan thong bao cho server da ket thuc viec upld
            s.recv(BUFFER_SIZE)

            #nhan thong bao nhan du file cua client
            msg = s.recv(BUFFER_SIZE).decode(FORMAT)
            if(msg == "FULL"):
                messagebox.showinfo("Success", f"File {file_name} uploaded successfully.")
            else:
                messagebox.showinfo("Failure", f"File {file_name} uploaded unsuccessfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error during file upload: {e}")
            s.send(b"ERROR")
def upld_folder():
    dir_path = filedialog.askdirectory(title="Select a Directory")
    

# Hàm liệt kê tệp
def list_files():
    try:
        s.sendall(b"LIST")
        number_of_files = struct.unpack("!i", s.recv(4))[0]
        print(number_of_files)
        file_list.delete(1.0, tk.END)  # Xóa danh sách cũ
        for _ in range(number_of_files):
            file_name_size = struct.unpack("i", s.recv(4))[0]

            s.send("ok".encode(FORMAT))

            file_name = s.recv(file_name_size).decode()

            s.send("ok".encode(FORMAT))
            file_size = struct.unpack("i", s.recv(4))[0]
            file_list.insert(tk.END, f"{file_name} - {file_size} bytes\n")
            s.sendall(b"1")
        total_directory_size = struct.unpack("i", s.recv(4))[0]
        file_list.insert(tk.END, f"Total directory size: {total_directory_size} bytes\n")
        s.sendall(b"1")
    except Exception as e:
        messagebox.showerror("Error", f"Error listing files: {e}")

# Hàm tải xuống file tu server ve client
def dwld():
    file_name = str(file_name_entry.get())
    print(file_name)
      # Lấy tên file từ giao diện người dùng
    if file_name:
        try:
            # Gửi yêu cầu tải xuống tệp
            s.sendall(b"DWLD")
            s.recv(BUFFER_SIZE)  # Nhận tín hiệu đồng bộ từ server
            # s.sendall(struct.pack("h", len(file_name)))  # Gửi độ dài tên file
            s.send(file_name.encode(FORMAT))  # Gửi tên file

            #TODO
            
            # Nhận kích thước file từ server interpret 4 byte dau tien
            buf = b''
            while len(buf) < 4:
                buf += s.recv(4 - len(buf))
            file_size = struct.unpack('!i', buf)[0]

            if file_size == -1:
                messagebox.showerror("Error", f"File {file_name} not found.")
                return
            #gui tb nhan ten file
            s.send("ok".encode(FORMAT))
            # Tạo file mới để ghi dữ liệu đã tải về
            
            print(file_size)
            #nhan file
            bytes_received = 0
            with open(f"downloaded_{file_name}", "wb") as f:
                print("Downloading...")
                while bytes_received < file_size:
                    data = s.recv(BUFFER_SIZE)  # Nhận dữ liệu
                    if not data or data == b"ERROR":
                        break
                    f.write(data)  # Ghi dữ liệu vào file
                    bytes_received += len(data)
            if bytes_received == file_size:
                messagebox.showinfo("Success", f"File {file_name} downloaded successfully.")
                s.send(f"Download {file_name} successful ".encode(FORMAT))
            else:
                s.send(b"ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"Error downloading file: {e}")

# Hàm xóa file
def delf():
    file_name = file_name_entry.get()
    if file_name:
        try:
            s.sendall(b"DELF")
            s.recv(BUFFER_SIZE)
            s.sendall(struct.pack("h", len(file_name)))
            s.sendall(file_name.encode())

            file_exists = struct.unpack("i", s.recv(4))[0]
            if file_exists == -1:
                messagebox.showerror("Error", f"File {file_name} not found.")
                return

            confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete {file_name}?")
            if confirm:
                s.sendall(b"Y")
                delete_status = struct.unpack("i", s.recv(4))[0]
                if delete_status == 1:
                    messagebox.showinfo("Success", f"File {file_name} deleted successfully.")
                else:
                    messagebox.showerror("Error", "Error deleting the file.")
            else:
                s.sendall(b"N")
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting file: {e}")

# Hàm thoát kết nối
def quit_app():
    try:
        s.sendall(b"QUIT")
        s.recv(BUFFER_SIZE)
        s.close()
        messagebox.showinfo("Disconnected", "Disconnected from the server.")
        root.quit()
    except Exception as e:
        messagebox.showerror("Error", f"Error during disconnection: {e}")

# Hàm chạy trong một thread riêng biệt cho các thao tác như tải lên, tải xuống
def run_task_in_thread(task_function):
    # task_thread = threading.Thread(target=task_function)
    # task_thread.start()
    task_function()

########
USER_CREDENTIALS = {
    "admin": "1",
    "user1": "1"
}
def check_server_open():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)  # Thời gian timeout khi kết nối (5 giây)
    try:
        # Cố gắng kết nối đến server
        s.connect((TCP_IP, TCP_PORT))
        s.close()  # Đóng kết nối nếu kết nối thành công
        return True  # Nếu kết nối thành công, trả về True
    except socket.error as e:
        return False  # Nếu kết nối không thành công, trả về False    
# Khởi tạo giao diện người dùng
def handle_login():
    username = username_entry.get()
    password = password_entry.get()
     # Kiểm tra trạng thái server
    if not check_server_open():  # Kiểm tra xem server đã mở chưa
        messagebox.showerror("Server Not Open", "The server is not open. Please start the server first.")
        return  # Dừng lại nếu server chưa mở
    # Check if the username and password are correct
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        #messagebox.showinfo("Login Successful", "Welcome to FTP Client!")
        conn()
        history_conn(username,s.getsockname()[1])
        login_window.destroy()  # Close login window
        create_main_window()  # Open main FTP client window
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")

def create_main_window():
    global file_list, file_name_entry, root  # Declare global variables

    root = tk.Tk()
    root.title("FTP Client")
    root.geometry("600x650")  # Cố định kích thước cửa sổ

    # Tiêu đề chính
    title_label = tk.Label(root, text="FTP Client", font=("Helvetica", 16, "bold"), fg="#4CAF50")
    title_label.pack(pady=20)

    # Frame chứa các nút chức năng
    button_frame = tk.LabelFrame(root, text="Functions", padx=10, pady=10, bg="#f2f2f2")
    button_frame.pack(padx=10, pady=10, fill="x")

    # Các nút chức năng
    upload_btn = tk.Button(button_frame, text="Upload File", width=20, command=lambda: run_task_in_thread(upld), bg="#4CAF50", fg="white", font=("Helvetica", 12))
    upload_btn.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

    list_btn = tk.Button(button_frame, text="List Files", width=20, command=lambda: run_task_in_thread(list_files), bg="#4CAF50", fg="white", font=("Helvetica", 12))
    list_btn.grid(row=0, column=1, pady=10, padx=10, sticky="ew")

    download_btn = tk.Button(button_frame, text="Download File", width=20, command=lambda: run_task_in_thread(dwld), bg="#4CAF50", fg="white", font=("Helvetica", 12))
    download_btn.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

    delete_btn = tk.Button(button_frame, text="Delete File", width=20, command=lambda: run_task_in_thread(delf), bg="#4CAF50", fg="white", font=("Helvetica", 12))
    delete_btn.grid(row=1, column=1, pady=10, padx=10, sticky="ew")

    quit_btn = tk.Button(button_frame, text="Quit", width=20, command=quit_app, bg="#f44336", fg="white", font=("Helvetica", 12))
    quit_btn.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

    # Frame chứa thông tin file
    file_frame = tk.LabelFrame(root, text="File Operations", padx=10, pady=10, bg="#f2f2f2")
    file_frame.pack(padx=10, pady=10, fill="x")

    # Nhập tên file
    file_name_label = tk.Label(file_frame, text="File Name:", bg="#f2f2f2", font=("Helvetica", 12))
    file_name_label.grid(row=0, column=0, pady=5, sticky="w")
    file_name_entry = tk.Entry(file_frame, width=50, font=("Helvetica", 12))
    file_name_entry.grid(row=0, column=1, pady=5, padx=10, sticky="ew")

    # Danh sách file
    file_list_label = tk.Label(file_frame, text="Files on Server:", bg="#f2f2f2", font=("Helvetica", 12))
    file_list_label.grid(row=1, column=0, pady=5, sticky="nw")
    file_list = tk.Text(file_frame, height=10, width=50, font=("Helvetica", 12))
    file_list.grid(row=1, column=1, pady=5, padx=10, sticky="ew")

    # Căn chỉnh lại để các phần tử trong grid có thể mở rộng
    file_frame.grid_rowconfigure(0, weight=1)
    file_frame.grid_rowconfigure(1, weight=1)
    file_frame.grid_columnconfigure(1, weight=1)

    # Căn chỉnh lại cho các nút trong button_frame
    button_frame.grid_rowconfigure(0, weight=1)
    button_frame.grid_rowconfigure(1, weight=1)
    button_frame.grid_rowconfigure(2, weight=1)
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    # Bắt đầu vòng lặp giao diện
    root.mainloop()

# Function to quit the application
def quit_app():
    root.quit()

def handle_signup():
    username = signup_username_entry.get()
    password = signup_password_entry.get()
    
    if username in USER_CREDENTIALS:
        messagebox.showerror("Sign Up Failed", "Username already exists.")
    else:
        USER_CREDENTIALS[username] = password
        messagebox.showinfo("Sign Up Successful", "Account created successfully!")
        signup_window.destroy()
        login_window.deiconify()


def open_signup_window():
    login_window.withdraw()  # Ẩn cửa sổ đăng nhập
    global signup_window, signup_username_entry, signup_password_entry

    signup_window = tk.Tk()
    signup_window.title("Sign Up")
    signup_window.geometry("450x400") 
    signup_window.resizable(width=False, height=False)

    # Tiêu đề
    signup_title = tk.Label(signup_window, text="Sign Up", font=("Helvetica", 18, "bold"))
    signup_title.pack(pady=20)

    # Frame chứa các ô nhập liệu và nút đăng ký
    frame = tk.Frame(signup_window)
    frame.pack(padx=30, pady=20, fill="both", expand=True)

    signup_username_label = tk.Label(frame, text="Username:", font=("Helvetica", 12))
    signup_username_label.grid(row=0, column=0, padx=5, pady=10, sticky="w")
    signup_username_entry = tk.Entry(frame, font=("Helvetica", 12))
    signup_username_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

    signup_password_label = tk.Label(frame, text="Password:", font=("Helvetica", 12))
    signup_password_label.grid(row=1, column=0, padx=5, pady=10, sticky="w")
    signup_password_entry = tk.Entry(frame, show="*", font=("Helvetica", 12))
    signup_password_entry.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

    signup_btn = tk.Button(frame, text="Sign Up", command=handle_signup, font=("Helvetica", 12), bg="#4CAF50", fg="white")
    signup_btn.grid(row=2, column=0, columnspan=2, pady=15, sticky="ew")

    signup_window.mainloop()

def create_login_window():
    global login_window, username_entry, password_entry

    login_window = tk.Tk()
    login_window.title("Login")
    login_window.geometry("450x400")
    login_window.resizable(width=False, height=False)

    # Tiêu đề
    login_title = tk.Label(login_window, text="Login", font=("Helvetica", 18, "bold"))
    login_title.pack(pady=20)

    # Frame chứa các ô nhập liệu và nút đăng nhập
    frame = tk.Frame(login_window)
    frame.pack(padx=30, pady=20, fill="both", expand=True)

    username_label = tk.Label(frame, text="Username:", font=("Helvetica", 12))
    username_label.grid(row=0, column=0, padx=5, pady=10, sticky="w")
    username_entry = tk.Entry(frame, font=("Helvetica", 12))
    username_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

    password_label = tk.Label(frame, text="Password:", font=("Helvetica", 12))
    password_label.grid(row=1, column=0, padx=5, pady=10, sticky="w")
    password_entry = tk.Entry(frame, show="*", font=("Helvetica", 12))
    password_entry.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

    login_btn = tk.Button(frame, text="Login", command=handle_login, font=("Helvetica", 12), bg="#4CAF50", fg="white")
    login_btn.grid(row=2, column=0, columnspan=2, pady=15, sticky="ew")

    signup_btn = tk.Button(frame, text="Sign Up", command=open_signup_window, font=("Helvetica", 12), bg="#007BFF", fg="white")
    signup_btn.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

    login_window.mainloop()

# Start the application with login window
create_login_window()
