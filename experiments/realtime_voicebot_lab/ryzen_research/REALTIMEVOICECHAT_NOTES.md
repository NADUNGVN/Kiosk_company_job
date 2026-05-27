# Ghi Chú RealtimeVoiceChat Cho Nhánh Ryzen

## Kết Luận Ngắn

`KoljaB/RealtimeVoiceChat` phù hợp để học kiến trúc realtime voice chat, nhưng
không nên đưa nguyên framework vào project ở giai đoạn hiện tại.

Lý do:

- Kiosk của dự án này cần Windows TTS local, trong khi RealtimeVoiceChat stream
  audio TTS từ backend về browser.
- Dự án gốc hướng tới web client bằng browser, còn kiosk runtime của mình là
  tiến trình Python local có camera, vision, microphone và TTS.
- Dependency của framework gốc nặng và gồm nhiều phần chưa cần cho baseline:
  `RealtimeSTT`, `RealtimeTTS`, torch, torchaudio, transformers.
- Repo gốc ghi rõ maintainer không còn hỗ trợ tích cực; vì vậy chỉ nên học ý
  tưởng và tự viết prototype nhỏ theo nhu cầu.

## Phần Nên Học

- WebSocket audio chunk streaming.
- Cách chia module STT, LLM và TTS.
- Turn detection và dynamic silence detection.
- Interruption handling khi người dùng chen lời.
- Session state cho hội thoại realtime.

## Phần Nên Khác Với Dự Án Gốc

- Kiosk không nhận audio TTS từ Ryzen; kiosk chỉ nhận `reply_text`.
- Kiosk dùng Windows 11 TTS local để đọc phản hồi.
- Máy Ryzen ưu tiên faster-whisper + RAG theo hướng dự án hiện tại.
- Client kiosk không phải browser mà là Python runtime riêng.

## Hướng Prototype Sau Khi TTS Probe Ổn

1. Làm baseline một hỏi một đáp.
2. Kiosk ghi audio lượt nói.
3. Ryzen chạy faster-whisper và RAG.
4. Ryzen trả `reply_text`.
5. Kiosk đọc bằng Windows TTS.
6. Sau đó mới thử stream audio realtime và interruption detection.

## Nguồn

- `https://github.com/KoljaB/RealtimeVoiceChat`
- `https://github.com/KoljaB/RealtimeVoiceChat/blob/main/README.md`
