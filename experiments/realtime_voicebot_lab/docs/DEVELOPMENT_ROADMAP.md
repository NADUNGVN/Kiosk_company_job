# Roadmap Thử Nghiệm Realtime Voicebot

## Giai Đoạn 1: Kiosk TTS Probe

Mục tiêu:

- Xác nhận Windows TTS cài sẵn trên kiosk có đọc được tiếng Việt ổn định không.
- Kiểm tra việc nhận text theo chunk/câu và đọc nối tiếp có đủ mượt không.
- Đo log cơ bản: nhận chunk, bắt đầu đọc, đọc xong.

Không làm trong giai đoạn này:

- Không WebSocket.
- Không gửi audio.
- Không chạy STT.
- Không chạy RAG.
- Không xử lý interruption.

## Giai Đoạn 2: Nghiên Cứu RealtimeVoiceChat

Mục tiêu:

- Học kiến trúc client-server realtime voice chat.
- Xác định phần nào có thể tái sử dụng: audio streaming, session state, turn
  detection, interruption handling.
- Không copy nguyên framework vào project khi chưa có prototype nhỏ.

## Giai Đoạn 3: Prototype Một Hỏi Một Đáp

Mục tiêu:

- Kiosk ghi một lượt audio.
- Gửi file/audio buffer sang máy Ryzen.
- Máy Ryzen chạy faster-whisper + RAG.
- Kiosk nhận `reply_text` và đọc bằng Windows TTS.

Đây là phương án baseline và là phương án chữa cháy nếu realtime interruption
không ổn định.

## Giai Đoạn 4: Prototype Realtime Streaming

Mục tiêu:

- Kiosk stream audio chunk sang máy Ryzen.
- Máy Ryzen xử lý STT bán realtime.
- RAG/LLM trả text từng phần hoặc từng câu.
- Kiosk đọc bằng Windows TTS local.
- Thử phát hiện người dùng ngắt chủ đích trong khi TTS đang đọc.

Các vấn đề cần đo:

- Latency audio chunk.
- Latency STT.
- Latency RAG/LLM.
- Latency từ `reply_text` đến TTS start.
- Tỷ lệ ngắt nhầm do nhiễu/echo.
- Tỷ lệ không ngắt khi người dùng thật sự nói.
