# Realtime Voicebot Lab

Thư mục này dùng để thử nghiệm tách pipeline voicebot thành hai phần:

- Kiosk: kiểm tra Windows TTS realtime/chunk bằng voice cài sẵn trên máy.
- Máy Ryzen: nghiên cứu kiến trúc realtime voice chat để chuẩn bị cho
  faster-whisper + RAG.

Ở bước hiện tại, lab có hai nhánh độc lập:

- `kiosk_tts_probe/`: kiểm tra Windows TTS cục bộ trên kiosk.
- `stt_zipformer_vi_server/`: kiểm tra STT tiếng Việt realtime bằng
  RealtimeSTT + Sherpa-ONNX Zipformer VI.

Chưa kết nối hai máy, chưa tích hợp RAG/LLM vào pipeline chính.

## Cấu Trúc

```text
experiments/realtime_voicebot_lab/
  docs/
    CURRENT_MACHINE_CONFIG.md
    DEVELOPMENT_ROADMAP.md
    REALTIMEVOICECHAT_RESEARCH.md
  kiosk_tts_probe/
    README.md
    requirements-kiosk.txt
    sample_reply_stream.txt
    windows_tts_realtime_probe.py
  stt_zipformer_vi_server/
    RealtimeSTT/
    server_app/
    models/
    backend_server.py
    backend_config.json
    terminal_demo.py
    requirements.txt
    WEBSOCKET_API.md
```

## Chạy Test TTS Trên Kiosk

Trên kiosk hoặc máy hiện tại:

```powershell
python experiments\realtime_voicebot_lab\kiosk_tts_probe\windows_tts_realtime_probe.py --list-voices
```

Chạy thử với voice tiếng Việt đã cài sẵn:

```powershell
python experiments\realtime_voicebot_lab\kiosk_tts_probe\windows_tts_realtime_probe.py --backend winrt --voice-contains "Microsoft An"
```

Nếu chạy sau khi chỉ pull riêng thư mục `kiosk_tts_probe` về kiosk:

```powershell
python kiosk_tts_probe\windows_tts_realtime_probe.py --backend winrt --voice-contains "Microsoft An"
```

## Chạy Test STT Zipformer VI

```powershell
cd D:\work\project_company\kiosk\experiments\realtime_voicebot_lab\stt_zipformer_vi_server

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Smoke test bằng wav mẫu:

```powershell
.\.venv\Scripts\python.exe .\terminal_demo.py --sample
```

Test microphone realtime:

```powershell
.\.venv\Scripts\python.exe .\terminal_demo.py
```

Chạy server WebSocket để test sau:

```powershell
.\.venv\Scripts\python.exe .\backend_server.py --print-config
.\.venv\Scripts\python.exe .\backend_server.py
```

Endpoint:

```text
http://127.0.0.1:8010
ws://127.0.0.1:8010/ws/transcribe
```

## Tài Liệu

- `docs/CURRENT_MACHINE_CONFIG.md`: cấu hình máy hiện tại.
- `docs/REALTIMEVOICECHAT_RESEARCH.md`: ghi chú nghiên cứu repo
  `KoljaB/RealtimeVoiceChat`.
- `docs/DEVELOPMENT_ROADMAP.md`: hướng phát triển từ TTS probe đến pipeline
  hai máy.
- `stt_zipformer_vi_server/WEBSOCKET_API.md`: giao thức STT WebSocket.
