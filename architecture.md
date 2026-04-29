kiosk/
│
├── 🖥️  frontend/                  # Tầng UI
│   ├── templates/                 # TẤT CẢ HTML templates (gom từ các app)
│   │   ├── base/                  # Layout, base.html
│   │   ├── customer/              # Màn hình kiosk, nhân viên
│   │   ├── QRcodes/               # Scan CCCD, form
│   │   └── voice_chatbot/
│   └── static/                    # TẤT CẢ CSS/JS/Images
│       ├── css/
│       ├── js/
│       └── images/
│
├── ⚙️  apps/                      # Tầng Backend (Django apps)
│   ├── customer/
│   │   ├── views.py               # Mỏng — chỉ HTTP in/out
│   │   ├── services.py            # [MỚI] Business logic
│   │   ├── models.py              # Data models
│   │   └── urls.py
│   ├── QRcodes/
│   │   ├── views.py               # Mỏng
│   │   ├── services.py            # [MỚI] CCCD parsing, QR, mail merge
│   │   └── ...
│   ├── api_rest/
│   ├── voice_chatbot/
│   ├── set_times/
│   └── home/                      # Từ apps/home/ → apps/home/
│
├── 🔧  core/                      # [MỚI] Shared modules
│   ├── hardware/
│   │   ├── printer.py             # XP-58C ESC/POS logic
│   │   ├── audio.py               # gTTS + sounddevice
│   │   └── rs485.py               # RS485 reader
│   └── utils.py                   # Hàm tiện ích chung
│
├── 🗄️  KIOSK_QUAN3/              # Config Django
├── 📜  scripts/                   # Launchers, tools
├── 🔒  certs/                     # SSL
├── 📁  media/                     # User uploads
└── 🚀  kiosk_q3.py                # Entry point
