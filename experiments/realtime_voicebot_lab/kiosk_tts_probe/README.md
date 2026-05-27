# Kiosk Windows TTS Realtime Probe

Thư mục này có thể push/pull riêng về kiosk để test Windows TTS cài sẵn trên
máy. Mục tiêu chỉ là kiểm tra khả năng đọc text theo chunk/câu gần realtime.

Không có kết nối mạng trong bước này. Script giả lập việc kiosk nhận được
`reply_text` realtime bằng cách đọc từng dòng trong `sample_reply_stream.txt`.

## Cài Đặt

Nếu venv chưa có `pyttsx3`:

```powershell
python -m pip install -r requirements-kiosk.txt
```

## Liệt Kê Voice

```powershell
python windows_tts_realtime_probe.py --list-voices
```

## Chạy Thử Với Voice Tiếng Việt

```powershell
python windows_tts_realtime_probe.py --voice-contains "Microsoft An"
```

Nếu muốn chỉnh tốc độ:

```powershell
python windows_tts_realtime_probe.py --voice-contains "Microsoft An" --rate 160
```

## Kết Quả Cần Quan Sát

- Voice có được chọn đúng không.
- Chunk đến liên tục có được đọc theo đúng thứ tự không.
- TTS có delay lớn trước khi bắt đầu đọc không.
- Khi câu dài/ngắn xen kẽ, âm thanh có bị giật hoặc nuốt chữ không.
