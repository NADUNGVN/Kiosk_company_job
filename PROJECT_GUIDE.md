# 🏛️ Kiosk Public Service System - Project Documentation

## 1. Tổng Quan (Overview)
Dự án **Kiosk** là một hệ thống phần mềm chuyên dụng chạy trên các trạm Kiosk đặt tại các cơ quan hành chính công (ví dụ: UBND Quận 3). Hệ thống hỗ trợ người dân thực hiện các dịch vụ như:
*   Lấy số thứ tự tự động.
*   Quét mã QR từ CCCD để điền thông tin tự động vào các tờ khai.
*   Trợ lý ảo bằng giọng nói (Voice Chatbot) để hướng dẫn thủ tục.
*   Tra cứu thông tin và đánh giá chất lượng dịch vụ.

---

## 2. Kiến Trúc Hệ Thống (Architecture)
Dự án áp dụng mô hình **Modular Monolith** (Đơn khối phân mô-đun) để đảm bảo tính gọn gàng và dễ mở rộng.

### Các lớp chính:
*   **Frontend Layer (`/frontend`)**: Tập trung toàn bộ giao diện, CSS, JS và hình ảnh. Không để templates nằm rải rác trong từng app backend.
*   **Backend Layer (`/backend`)**: Chứa các Django apps thực hiện logic nghiệp vụ.
*   **Core Layer (`/core`)**: Chứa các module dùng chung và logic điều khiển phần cứng (Hardware abstraction).
*   **Infrastructure & Config (`/config`, `/scripts`)**: Cấu hình hệ thống, biến môi trường và các công cụ hỗ trợ vận hành.

---

## 3. Danh Mục Công Nghệ (Tech Stack)
*   **Ngôn ngữ chính**: Python 3.10+
*   **Framework**: Django 5.0.6
*   **Real-time**: Django Channels (WebSocket) & Uvicorn/Daphne.
*   **AI/Voice**: 
    *   TensorFlow (Nhận diện khuôn mặt/xử lý ảnh).
    *   gTTS (Chuyển văn bản thành giọng nói).
    *   SpeechRecognition (Nhận diện giọng nói).
*   **Frontend**: HTML5, Vanilla JS, Bootstrap, jQuery (Tối ưu cho màn hình cảm ứng).

---

## 4. Cấu Trúc Thư Mục (Directory Structure)

```text
kiosk/
├── 📁 backend/                # Logic nghiệp vụ (Django Apps)
│   ├── 📁 customer/           # Quản lý số thứ tự, khách hàng, đánh giá
│   ├── 📁 QRcodes/            # Xử lý quét CCCD và Mail Merge tờ khai
│   ├── 📁 voice_chatbot/      # Trợ lý ảo AI
│   ├── 📁 api_rest/           # API cung cấp dữ liệu cho Dashboard
│   └── 📁 apps/               # Các app bổ trợ (Home, Authentication)
├── 📁 frontend/               # Giao diện tập trung
│   ├── 📁 templates/          # Tất cả file HTML
│   └── 📁 static/             # Tất cả CSS, JS, Images
├── 📁 core/                   # Modules dùng chung
│   ├── 📁 hardware/           # Điều khiển máy in, RS485, Sound
│   └── 📄 utils.py            # Tiện ích hệ thống
├── 📁 config/                 # Cấu hình Django (Settings, URLs)
├── 📁 scripts/                # Scripts vận hành và bảo trì
├── 📁 media/                  # Dữ liệu người dùng tải lên (Audio, Banners)
├── 📁 certs/                  # Chứng chỉ SSL (HTTPS cho Microphone)
└── 📄 kiosk_q3.py             # Script Launcher tự động cho máy Kiosk
```

---

## 5. Các Tính Năng Cốt Lõi (Key Features)

### 5.1. Hệ thống Lấy số (`customer`)
*   Người dân chọn dịch vụ trên màn hình cảm ứng.
*   Hệ thống sinh số thứ tự và gọi lệnh in thông qua máy in nhiệt (XP-58C).
*   Dữ liệu được cập nhật real-time lên bảng hiển thị của nhân viên.

### 5.2. Quét mã QR & Tự động điền form (`QRcodes`)
*   Sử dụng Camera để quét mã QR trên CCCD.
*   Tự động tách thông tin (Họ tên, ngày sinh, địa chỉ).
*   Sử dụng `Mail Merge` để điền thông tin vào các mẫu đơn Word/PDF có sẵn.

### 5.3. Trợ lý ảo giọng nói (`voice_chatbot`)
*   Người dân nói chuyện trực tiếp với Kiosk.
*   Hệ thống nhận diện giọng nói -> Xử lý NLP -> Phản hồi bằng giọng nói tiếng Việt.
*   Hỗ trợ hướng dẫn các thủ tục hành chính phức tạp.

---

## 6. Tích Hợp Phần Cứng (Hardware Integration)
Tọa lạc tại `/core/hardware/`:
*   **Printer (`printer.py`)**: Giao tiếp qua ESC/POS lệnh in cho máy in nhiệt.
*   **RS485 (`rs485.py`)**: Đọc dữ liệu từ các cảm biến hoặc thiết bị ngoại vi qua cổng Serial.
*   **Audio (`audio.py`)**: Quản lý phát âm thanh hướng dẫn.

---

## 7. Hướng Dẫn Vận Hành (Operations Guide)

### 7.1. Môi trường phát triển (Local)
1. Kích hoạt venv: `.\.venv\Scripts\activate`
2. Chạy server SSL: `python manage.py runsslserver 0.0.0.0:8000`

### 7.2. Chạy tự động trên máy Kiosk
Sử dụng file `kiosk_q3.py` để hệ thống tự động kiểm tra cổng, giải phóng tiến trình cũ, khởi động server và mở trình duyệt ở chế độ toàn màn hình.

---
*Tài liệu được cập nhật lần cuối vào: 22/04/2026*
