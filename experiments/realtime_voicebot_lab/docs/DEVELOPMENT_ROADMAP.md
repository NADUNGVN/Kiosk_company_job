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

### Mục tiêu:
- Kiosk stream audio chunk sang máy Ryzen/Laptop. (Đã thiết lập thành công kết nối WebSocket LAN cổng `8012` và stream audio nhị phân thô từ mic Kiosk sang).
- Máy Ryzen/Laptop xử lý STT bán realtime. (Đã đánh giá hoàn thiện mô hình STT Zipformer tiếng Việt chạy local).
- Hiển thị kết quả: Laptop không mở mic, chỉ nhận dữ liệu từ WebSocket, chạy STT và in trực tiếp kết quả nhận dạng lên terminal Laptop dưới dạng Final text hoàn chỉnh, cập nhật nối tiếp mượt mượt (y hệt demo của repo `RealtimeSTT`).
- RAG/LLM trả text từng phần hoặc từng câu. (Đã hoàn thành tích hợp Ollama Qwen2.5:7b).

### Kết quả & Xác minh:
- **Độ trễ truyền gói nhị phân (LAN Latency)**: Đã xác minh RTT mạng LAN ổn định ở mức cực thấp (~0.5ms - 2ms).
- **Tính trọn vẹn dữ liệu (Data Integrity)**: Audio chunk 96,000 bytes truyền qua LAN nguyên vẹn, server lưu file WAV không bị gián đoạn hay vấp.
- **Latency STT**: Thời gian nhận dạng câu hoàn chỉnh (Final) từ khi dứt lời đạt độ chính xác 100%.
- **Trạng thái**: **Hoàn Thành**

---

## Giai Đoạn 5: Laptop TTS Integration (Tích hợp phát loa Laptop)

> [!IMPORTANT]
> **TRẠNG THÁI HIỆN TẠI (CURRENT PHASE)**: Dự án đang ở giai đoạn này.

### Mục tiêu:
- Tải và cài đặt thành công model `qwen2.5:7b` không chứa chế độ suy nghĩ ngầm để tốc độ trả token đạt tốc độ siêu tốc.
- Triển khai Windows SAPI SpVoice trực tiếp trên Laptop thông qua môi trường ảo (đã cài đặt `pywin32` thành công).
- Tích hợp pipeline gom câu (Sentence Buffering) từ repo `RealtimeVoiceChat`. Server gom các token LLM thành câu hoàn chỉnh dựa trên các dấu ngắt câu (`.`, `,`, `?`, `!`, `\n`) và đẩy lập tức vào hàng đợi phát âm thanh SAPI.
- Tích hợp cơ chế ngắt lời chủ động (Interruption): Khi có câu hỏi STT Final mới, loa Laptop lập tức ngắt tiếng cũ (`SpVoice.Speak("", 2)`) để trả lời câu mới, tăng tính phản xạ tự nhiên.

### Các vấn đề đã xác minh & cần đo:
- `[x]` Triệt tiêu hoàn toàn rác chữ tiếng Trung bằng cách chuẩn hóa Prompt hệ thống (System Prompt) bằng tiếng Việt thuần khiết.
- `[x]` Hàng đợi TTS chạy ẩn hoạt động ổn định, đọc mượt mà tuần tự từng câu.
- `[x]` Cơ chế ngắt lời lập tức khi có câu hỏi mới phản xạ chính xác.
- `[ ]` Thử nghiệm thực tế luồng tương tác thoại hai chiều và đo đạc trải nghiệm người dùng.
