import subprocess
import webbrowser
import time
import requests
import os
import threading
import signal
import sys
import psutil
import socket
from pathlib import Path
from dotenv import load_dotenv
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Cấu hình
BASE_DIR = Path(__file__).resolve().parent
HEALTH_CHECK_URL = os.getenv('HEALTH_CHECK_URL', 'https://127.0.0.1:8000')
VENV_ACTIVATE = os.path.join(os.getcwd(), "venv", "Scripts", "activate.bat")
SSL_KEYFILE = os.path.join(BASE_DIR, 'certs', 'key.pem')
SSL_CERTFILE = os.path.join(BASE_DIR, 'certs', 'cert.pem')
PORT = 8000
MAX_RESTART_ATTEMPTS = 3
RESTART_COOLDOWN = 60

# Biến toàn cục
uvicorn_process = None
restart_count = 0
last_restart_time = 0
shutdown_event = threading.Event()

def find_process_by_port(port):
    """Tìm tất cả các tiến trình đang sử dụng port"""
    try:
        # Sử dụng netstat để lấy thông tin chi tiết
        output = subprocess.check_output(
            f'netstat -ano | findstr :{port}',
            shell=True
        ).decode()
        
        pids = set()
        for line in output.split('\n'):
            if line.strip():
                try:
                    # Lấy PID từ cột cuối cùng
                    pid = int(line.strip().split()[-1])
                    pids.add(pid)
                except (ValueError, IndexError):
                    continue
        return list(pids)
    except subprocess.CalledProcessError:
        return []

def is_port_available(port):
    """Kiểm tra xem port có thực sự available không"""
    try:
        # Thử bind vào port để kiểm tra
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('0.0.0.0', port))
            return True
    except (socket.error, OSError):
        return False
    finally:
        try:
            s.close()
        except:
            pass

def force_kill_process(pid):
    """Kill process một cách mạnh mẽ"""
    try:
        process = psutil.Process(pid)
        
        # Kill các tiến trình con trước
        children = process.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        
        # Kill tiến trình cha
        process.kill()
        
        # Đợi tiến trình kết thúc
        process.wait(timeout=5)
        return True
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        return False
    except Exception as e:
        print(f"Lỗi khi kill process {pid}: {e}")
        return False

def ensure_port_free():
    """Đảm bảo port được giải phóng hoàn toàn"""
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        if is_port_available(PORT):
            print(f"Cổng {PORT} đã sẵn sàng")
            return True
            
        print(f"Tìm và giải phóng các tiến trình đang sử dụng cổng {PORT}...")
        pids = find_process_by_port(PORT)
        
        if not pids:
            print(f"Không tìm thấy tiến trình nào đang sử dụng cổng {PORT}")
            time.sleep(2)
            attempt += 1
            continue
            
        for pid in pids:
            print(f"Tìm thấy tiến trình {pid} đang sử dụng cổng {PORT}")
            if force_kill_process(pid):
                print(f"Đã kill tiến trình {pid}")
            else:
                print(f"Không thể kill tiến trình {pid}")
        
        # Đợi các tiến trình được giải phóng hoàn toàn
        time.sleep(2)
        attempt += 1
    
    return is_port_available(PORT)

def run_uvicorn():
    global uvicorn_process
    
    if not ensure_port_free():
        raise RuntimeError(f"Không thể giải phóng cổng {PORT} sau nhiều lần thử")
    
    print("Khởi động Uvicorn...")
    try:
        startup_command = f'cmd.exe /k "{VENV_ACTIVATE} && uvicorn config.asgi:application --host 0.0.0.0 --port {PORT} --ssl-keyfile "{SSL_KEYFILE}" --ssl-certfile "{SSL_CERTFILE}""'
        uvicorn_process = subprocess.Popen(
            startup_command,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
        
        # Đợi và kiểm tra xem server có start thành công không
        time.sleep(5)
        if not check_server_running():
            raise RuntimeError("Server không khởi động được")
            
    except Exception as e:
        print(f"Lỗi khởi động Uvicorn: {e}")
        if uvicorn_process:
            force_kill_process(uvicorn_process.pid)
        raise

def check_server_running():
    """Kiểm tra xem server có đang chạy không"""
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def check_connection():
    global restart_count, last_restart_time
    while not shutdown_event.is_set():
        try:
            if check_server_running():
                print("Server đang hoạt động bình thường.")
                restart_count = 0
            else:
                print("Server không phản hồi.")
                handle_restart()
        except Exception as e:
            print(f"Lỗi kiểm tra kết nối: {e}")
            handle_restart()
        time.sleep(20)

def handle_restart():
    global restart_count, last_restart_time
    
    current_time = time.time()
    if current_time - last_restart_time < RESTART_COOLDOWN:
        print(f"Đợi {RESTART_COOLDOWN} giây trước khi restart...")
        return
    
    if restart_count < MAX_RESTART_ATTEMPTS:
        print(f"Thử restart lần {restart_count + 1}/{MAX_RESTART_ATTEMPTS}")
        try:
            if uvicorn_process:
                force_kill_process(uvicorn_process.pid)
            ensure_port_free()
            run_uvicorn()
            restart_count += 1
            last_restart_time = current_time
        except Exception as e:
            print(f"Lỗi khi restart: {e}")
    else:
        print("Đã vượt quá số lần restart cho phép.")
        shutdown_event.set()

def cleanup():
    print("Dọn dẹp trước khi thoát...")
    shutdown_event.set()
    if uvicorn_process:
        force_kill_process(uvicorn_process.pid)
    ensure_port_free()

def signal_handler(signum, frame):
    cleanup()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Đảm bảo cổng trống trước khi bắt đầu
        if not ensure_port_free():
            print("Không thể giải phóng cổng, thoát chương trình")
            return
        
        # Khởi động ban đầu
        run_uvicorn()
        
        # Khởi động thread kiểm tra
        monitor_thread = threading.Thread(target=check_connection, daemon=True)
        monitor_thread.start()
        
        # Mở trình duyệt
        time.sleep(5)
        webbrowser.open(f'{HEALTH_CHECK_URL}/chon_dich_vu')
        
        while not shutdown_event.is_set():
            time.sleep(1)
            
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"Lỗi không mong đợi: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()