# Kiến Trúc Đề Xuất: Voicebot Phân Tán Giữa Kiosk Và Máy Xử Lý AI

## 1. Mục Tiêu Kiến Trúc

Hướng phát triển hiện tại là tách hệ thống thành hai lớp tính toán:

- Kiosk tại hiện trường chịu trách nhiệm tương tác trực tiếp với người dùng.
- Máy xử lý AI mạnh hơn chịu trách nhiệm cho các tác vụ nặng như STT và RAG.

Cách chia này phù hợp với điều kiện phần cứng hiện tại: kiosk dùng CPU
i5-4250U, không phù hợp để chạy các mô hình nặng theo thời gian thực, trong khi
máy Ryzen 9HX + RTX 5060 có đủ tài nguyên để xử lý faster-whisper và pipeline
truy xuất/ngôn ngữ.

## 2. Vai Trò Của Từng Thiết Bị

### Kiosk i5-4250U

Kiosk là thiết bị tương tác tại điểm phục vụ, ưu tiên độ ổn định, phản hồi nhanh
và vận hành độc lập với giao diện người dùng.

Các nhiệm vụ chính:

- Camera input.
- Computer vision để phát hiện người cần hỗ trợ.
- Ghi âm từ microphone.
- Gửi audio realtime sang máy xử lý AI.
- Nhận `reply_text` từ máy xử lý AI.
- Đọc phản hồi bằng Windows 11 TTS có sẵn trên máy.

Kiosk không nên chạy các mô hình nặng như faster-whisper, RAG hoặc LLM cục bộ,
vì điều này có thể làm giảm FPS vision, tăng latency giao diện và ảnh hưởng đến
trải nghiệm tại máy.

### Máy Ryzen 9HX + RTX 5060

Máy AI đóng vai trò xử lý suy luận nặng và có thể đặt trong cùng mạng nội bộ.

Các nhiệm vụ chính:

- Nhận audio realtime từ kiosk qua Ethernet.
- Chạy faster-whisper để chuyển speech thành text.
- Chạy RAG để truy xuất tri thức nghiệp vụ.
- Sinh `reply_text` cho kiosk.
- Trả kết quả về kiosk qua mạng nội bộ.

Máy AI không trực tiếp phát âm thanh cho người dùng. Điều này giúp âm thanh luôn
phát từ đúng kiosk đang tương tác với khách.

## 3. Kết Nối Mạng

Hai máy kết nối qua Ethernet trong mạng nội bộ.

Yêu cầu của kết nối:

- Latency thấp và ổn định hơn Wi-Fi.
- Không phụ thuộc Internet cho việc truyền audio giữa hai máy.
- Cho phép triển khai giao thức realtime hoặc near-realtime.
- Có thể mở rộng về sau nếu một máy AI phục vụ nhiều kiosk.

Các giao thức có thể thử nghiệm:

- WebSocket cho audio chunk realtime và event hai chiều.
- HTTP streaming nếu muốn đơn giản hóa server/client.
- REST request/response cho phương án một hỏi một đáp.

## 4. Pipeline Realtime Mục Tiêu

Pipeline mục tiêu:

1. Kiosk dùng camera và computer vision để phát hiện người có khả năng cần hỗ
   trợ.
2. Khi trạng thái đạt `NEED_SUPPORT`, kiosk bắt đầu ghi âm.
3. Kiosk gửi audio realtime sang máy Ryzen qua Ethernet.
4. Máy Ryzen chạy faster-whisper để tạo transcript.
5. Transcript được đưa vào RAG/chatbot để sinh câu trả lời.
6. Máy Ryzen trả `reply_text` về kiosk.
7. Kiosk dùng Windows 11 TTS đọc câu trả lời.
8. Vision tiếp tục theo dõi để quyết định duy trì hoặc đóng phiên.

Trong kiến trúc này, computer vision là lớp gating đầu vào của hội thoại. Nó
giúp tránh trường hợp chatbot bắt đầu lắng nghe khi người chỉ đi ngang hoặc
không có ý định sử dụng kiosk.

## 5. Vấn Đề Thử Nghiệm 01: Voicebot Realtime Có Khả Năng Ngắt Chủ Đích

Mục tiêu của thử nghiệm này là kiểm tra voicebot realtime có thể xử lý tình
huống người dùng chủ động ngắt lời hay không.

Khái niệm “ngắt chủ đích” cần phân biệt với nhiễu:

- Ngắt chủ đích: người dùng bắt đầu nói rõ ràng trong khi hệ thống đang nói hoặc
  đang chờ hoàn tất lượt xử lý.
- Nhiễu môi trường: tiếng nền, tiếng người khác, tiếng va chạm, tiếng loa vọng,
  hoặc âm thanh không hướng đến kiosk.

Các câu hỏi nghiên cứu:

- Kiosk có phát hiện được người dùng đang nói trong lúc TTS đang phát không?
- Hệ thống có nên dừng TTS ngay khi phát hiện speech mới không?
- Làm sao phân biệt speech thật với nhiễu để tránh ngắt nhầm?
- faster-whisper trên máy Ryzen có đủ nhanh để tạo transcript bán realtime
  không?
- Latency tổng từ lúc người dùng nói đến lúc kiosk phản hồi là bao nhiêu?

Các chỉ số cần đo:

- Latency audio chunk từ kiosk sang máy Ryzen.
- Latency STT.
- Latency RAG/chatbot.
- Latency từ `reply_text` đến lúc Windows TTS bắt đầu đọc.
- Tỷ lệ ngắt nhầm do nhiễu.
- Tỷ lệ không ngắt khi người dùng thật sự muốn nói.

Issue chính:

- Nếu không có VAD hoặc rule phân biệt speech/nhiễu tốt, hệ thống dễ ngắt TTS
  sai.
- Nếu latency STT/RAG quá cao, realtime sẽ tạo cảm giác chậm và thiếu tự nhiên.
- Nếu TTS đang phát từ loa gần microphone, hệ thống có thể nghe lại chính giọng
  của mình và hiểu nhầm là người dùng đang nói.

## 6. Vấn Đề Thử Nghiệm 02: Phương Án Dự Phòng Một Hỏi Một Đáp

Nếu voicebot realtime có khả năng ngắt chủ đích không đạt yêu cầu ổn định, hệ
thống chuyển sang phương án dự phòng: một hỏi một đáp.

Pipeline dự phòng:

1. Kiosk phát hiện `NEED_SUPPORT`.
2. Kiosk phát lời chào bằng Windows TTS.
3. Kiosk mở ghi âm trong một khoảng thời gian rõ ràng.
4. Người dùng nói xong.
5. Kiosk gửi toàn bộ audio lượt đó sang máy Ryzen.
6. Máy Ryzen chạy STT + RAG.
7. Máy Ryzen trả `reply_text`.
8. Kiosk đọc câu trả lời.
9. Kiosk hỏi người dùng có cần hỗ trợ thêm không.
10. Nếu có, lặp lại lượt mới; nếu không, đóng phiên.

Ưu điểm:

- Đơn giản hơn realtime.
- Dễ kiểm soát trạng thái.
- Ít bị ảnh hưởng bởi echo giữa loa và microphone.
- Dễ log và đánh giá từng lượt hội thoại.

Nhược điểm:

- Trải nghiệm kém tự nhiên hơn voicebot realtime.
- Người dùng phải đợi hệ thống nói xong hoặc chờ đến lượt nói.
- Không xử lý tốt tình huống người dùng ngắt lời giữa chừng.

## 7. Interface Đề Xuất Giữa Hai Máy

Ở giai đoạn thử nghiệm, nên giữ interface tối giản và dễ debug.

### Kiosk gửi sang máy Ryzen

Thông tin tối thiểu:

- `session_id`: mã phiên tương tác.
- `turn_id`: mã lượt hội thoại.
- `audio_chunk` hoặc `audio_file`.
- `sample_rate`.
- `timestamp`.
- `vision_state`: ví dụ `NEED_SUPPORT`, `SESSION_OPEN`, `SESSION_CLOSING`.

### Máy Ryzen trả về kiosk

Thông tin tối thiểu:

- `session_id`.
- `turn_id`.
- `transcript`.
- `reply_text`.
- `confidence` nếu có.
- `is_final`.
- `error` nếu xử lý thất bại.

Kiosk chỉ cần `reply_text` để đọc bằng Windows 11 TTS, nhưng nên log thêm
`transcript` để đánh giá chất lượng STT và chatbot.

## 8. Liên Hệ Với Các Thử Nghiệm Vision Hiện Tại

Hai thử nghiệm vision hiện tại cung cấp lớp quyết định khi nào nên bắt đầu
voicebot:

- Thử nghiệm 01: MediaPipe Tasks `PoseLandmarker + FaceLandmarker`.
- Thử nghiệm 02: MediaPipe Holistic legacy.

Kết quả hiện tại cho thấy MediaPipe Tasks nhẹ hơn và phù hợp hơn với kiosk i5.
Holistic hữu ích cho nghiên cứu mắt/iris/gaze nhưng tiêu tốn RAM và CPU cao hơn.

Do đó, hướng triển khai thực tế nên là:

- Kiosk chạy MediaPipe Tasks hoặc rule vision nhẹ.
- Máy Ryzen chạy faster-whisper và RAG.
- Holistic giữ vai trò công cụ nghiên cứu, không phải runtime chính mặc định.

## 9. Hướng Phát Triển Tiếp Theo

Các bước nên làm tiếp theo:

- Thiết kế server nhận audio trên máy Ryzen.
- Thiết kế client gửi audio từ kiosk qua Ethernet.
- Thử nghiệm phương án một hỏi một đáp trước để có baseline ổn định.
- Sau khi baseline ổn, thử realtime streaming và interruption detection.
- Bổ sung VAD hoặc rule energy/speech để phân biệt người dùng nói với nhiễu.
- Kiểm tra echo khi Windows TTS phát ra loa và microphone đang mở.
- Chuẩn hóa log theo `session_id`, `turn_id`, `vision_state`, `transcript`,
  `reply_text`, latency và lỗi.
