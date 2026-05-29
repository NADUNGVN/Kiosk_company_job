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

> [!IMPORTANT]
> **TRẠNG THÁI HIỆN TẠI (CURRENT PHASE)**: Dự án đang ở giai đoạn này.

### Mục tiêu:
- Kiosk stream audio chunk sang máy Ryzen/Laptop. (Đã thiết lập thành công kết nối WebSocket LAN cổng `8012` và stream audio nhị phân thô từ mic Kiosk sang).
- Máy Ryzen/Laptop xử lý STT bán realtime. (Đã đánh giá hoàn thiện mô hình STT Zipformer tiếng Việt chạy local).
- Hiển thị kết quả: Laptop không mở mic, chỉ nhận dữ liệu từ WebSocket, chạy STT và in trực tiếp kết quả nhận dạng lên terminal Laptop dưới dạng Final text hoàn chỉnh, cập nhật nối tiếp mượt mà (y hệt demo của repo `RealtimeSTT`).
- RAG/LLM trả text từng phần hoặc từng câu. (Bước tiếp theo).
- Kiosk đọc bằng Windows TTS local. (Bước tiếp theo).
- Thử phát hiện người dùng ngắt chủ đích trong khi TTS đang đọc (Interruption).

### Các vấn đề cần đo & đã xác minh:
- **Độ trễ truyền gói nhị phân (LAN Latency)**: Đã xác minh RTT mạng LAN ổn định ở mức cực thấp (~0.5ms - 2ms).
- **Tính trọn vẹn dữ liệu (Data Integrity)**: Audio chunk 96,000 bytes truyền qua LAN nguyên vẹn, server lưu file WAV không bị gián đoạn hay vấp.
- **Latency STT**: Thời gian nhận dạng câu hoàn chỉnh (Final) từ khi dứt lời.
- **Latency RAG/LLM**.
- **Latency từ `reply_text` đến TTS start**.
- **Tỷ lệ ngắt nhầm do nhiễu/echo**.
- **Tỷ lệ không ngắt khi người dùng thật sự nói**.
