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

Script sẽ liệt kê hai nhóm:

- `SAPI`: voice desktop mà `pyttsx3` dùng được, thường chỉ thấy David/Zira.
- `WinRT / OneCore`: voice Windows modern trong Settings, thường có
  `Microsoft An`.

## Chạy Thử Với Voice Tiếng Việt

```powershell
python windows_tts_realtime_probe.py --backend winrt --voice-contains "Microsoft An"
```

Nếu muốn chỉnh tốc độ:

```powershell
python windows_tts_realtime_probe.py --backend winrt --voice-contains "Microsoft An" --rate 160
```

Nếu dùng voice SAPI như David/Zira:

```powershell
python windows_tts_realtime_probe.py --backend sapi --voice-contains "Zira"
```

## Khi Registry Có Microsoft An Nhưng WinRT Không Thấy

Một số máy kiosk có `MSTTS_V110_viVN_An` trong registry OneCore, nhưng Python
WinRT vẫn trả về rỗng. Khi đó `--backend winrt` không dùng được và `pyttsx3`
cũng không thấy `Microsoft An` vì voice chưa được expose sang SAPI.

Có thể thử expose voice OneCore sang SAPI bằng PowerShell Admin:

```powershell
powershell -ExecutionPolicy Bypass -File .\expose_onecore_voice_to_sapi.ps1
```

Sau đó đóng/mở lại terminal và kiểm tra:

```powershell
python windows_tts_realtime_probe.py --list-voices
python windows_tts_realtime_probe.py --backend sapi --voice-contains "Microsoft An"
```

Script sẽ backup registry token trước khi copy vào thư mục
`kiosk_tts_probe/registry_backups/`.

## Kết Quả Cần Quan Sát

- Voice có được chọn đúng không.
- Chunk đến liên tục có được đọc theo đúng thứ tự không.
- TTS có delay lớn trước khi bắt đầu đọc không.
- Khi câu dài/ngắn xen kẽ, âm thanh có bị giật hoặc nuốt chữ không.
