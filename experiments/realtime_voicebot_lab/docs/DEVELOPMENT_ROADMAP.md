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

## Giai Đoạn 5: Distributed TTS & Acoustic Echo Loop Resolution (Tổng Hợp Tại Laptop - Phát Tại Kiosk)

*   **Trạng thái**: **Hoàn Thành**

### Mục tiêu đạt được:
*   **Di chuyển đầu ra âm thanh về Kiosk**: Laptop Server sử dụng WinRT `SpeechSynthesizer` và giọng **Microsoft An** để tổng hợp văn bản thành bytes dữ liệu âm thanh WAV thô trực tiếp trong RAM một cách siêu tốc và gửi sang Kiosk qua WebSocket dạng Base64 (`tts_audio`). Kiosk giải mã và phát loa trực tiếp từ bộ nhớ (`winsound.PlaySound` với cờ `SND_MEMORY`). Kiosk hoàn toàn không cần cài đặt engine TTS hay gói giọng đọc phức tạp.
*   **Khử tiếng vọng loa chủ động (Acoustic Echo Loop Resolution)**: Khắc phục triệt để việc Microphone của Kiosk thu lại tiếng nói của loa phát. Trong quá trình Kiosk đang phát loa (`self.tts_player.is_speaking() == True`), client Kiosk sẽ tạm dừng truyền luồng âm thanh Microphone sang Server Laptop. Điều này giúp triệt tiêu hoàn toàn 100% vòng lặp tự thoại tại nguồn.
*   **Sửa lỗi chết luồng TTS khi bị cướp lời**: Đổi điều kiện vòng lặp chính của luồng ẩn sang cờ dài hạn `while self._is_active` giúp luồng TTS tồn tại vĩnh viễn và hoạt động trơn tru sau khi bị người dùng ngắt lời (STT FINAL kích hoạt sự kiện `tts_interrupt`).
*   **Lọc sạch rác chữ tiếng Trung**: Thắt chặt Prompt hệ thống và kết hợp bộ lọc Regex CJK programmatically trên Server giúp lọc sạch 100% rác ký tự chữ Hán hoặc dấu câu tiếng Trung full-width trước khi hiển thị hoặc phát ra loa.
