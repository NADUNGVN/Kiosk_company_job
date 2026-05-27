# Realtime Voicebot Lab

Thư mục này dùng để thử nghiệm tách pipeline voicebot thành hai phần:

- Kiosk: kiểm tra Windows TTS realtime/chunk bằng voice cài sẵn trên máy.
- Máy Ryzen: nghiên cứu kiến trúc realtime voice chat để chuẩn bị cho
  faster-whisper + RAG.

Ở bước hiện tại, chỉ triển khai test TTS cục bộ cho kiosk. Chưa kết nối hai máy,
chưa chạy faster-whisper, chưa tích hợp RAG.

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
  ryzen_research/
    README.md
    REALTIMEVOICECHAT_NOTES.md
```

## Chạy Test TTS Trên Kiosk

Trên kiosk hoặc máy hiện tại:

```powershell
python experiments\realtime_voicebot_lab\kiosk_tts_probe\windows_tts_realtime_probe.py --list-voices
```

Chạy thử với voice tiếng Việt đã cài sẵn:

```powershell
python experiments\realtime_voicebot_lab\kiosk_tts_probe\windows_tts_realtime_probe.py --voice-contains "Microsoft An"
```

Nếu chạy sau khi chỉ pull riêng thư mục `kiosk_tts_probe` về kiosk:

```powershell
python kiosk_tts_probe\windows_tts_realtime_probe.py --voice-contains "Microsoft An"
```

## Tài Liệu

- `docs/CURRENT_MACHINE_CONFIG.md`: cấu hình máy hiện tại.
- `docs/REALTIMEVOICECHAT_RESEARCH.md`: ghi chú nghiên cứu repo
  `KoljaB/RealtimeVoiceChat`.
- `docs/DEVELOPMENT_ROADMAP.md`: hướng phát triển từ TTS probe đến pipeline
  hai máy.
