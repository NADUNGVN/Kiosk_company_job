# Xây dựng Kiosk Tự Động Giao Tiếp Với Người Dân Qua Xử Lý Hình Ảnh Và Ngôn Ngữ Tự Nhiên
*(Design Autonomous Interactive Kiosk for Citizen Services Using Image and Natural Language Processing)*

Tài liệu này là **Tổng quan dự án chung** cho các thử nghiệm đang diễn ra tại thư mục `experiments/`. Dự án hướng tới xây dựng một hệ thống Kiosk thông minh tự động hỗ trợ dịch vụ công cho người dân thông qua sự kết hợp của thị giác máy tính (Computer Vision) và xử lý ngôn ngữ tự nhiên giọng nói thời gian thực (Realtime Voicebot).

---

## 1. Kiến Trúc Hệ Thống Phân Tán (Distributed Architecture)

Để đảm bảo hiệu năng tối đa và tính ổn định cao, dự án áp dụng mô hình phân tán **hai máy** kết nối qua mạng nội bộ Ethernet LAN (WebSocket):

*   **Máy Kiosk (Thiết bị đầu cuối)**: Cấu hình vừa phải, chịu trách nhiệm cho các tác vụ tương tác vật lý trực tiếp với người dân:
    *   Mở Camera thu hình ảnh để nhận diện sự hiện diện.
    *   Bật Microphone ghi âm giọng nói của người dân để stream sang Laptop.
    *   *Phát loa trả lời (Phương án dự kiến)*: Đề xuất sử dụng Windows TTS cục bộ. Quy trình và cách thức phát loa chi tiết sẽ được kiểm thử và xây dựng sau khi phần LLM hoàn tất.
*   **Máy Laptop/Ryzen (Máy chủ xử lý nặng - GPU RTX 5060)**: Chịu trách nhiệm chạy các mô hình AI lớn và nặng:
    *   Nhận luồng âm thanh nhị phân qua WebSocket, chạy mô hình nhận dạng tiếng Việt **Zipformer STT**.
    *   Xử lý suy nghĩ, tra cứu cơ sở dữ liệu tri thức **LLM RAG** và trả về kết quả dạng stream (SSE).

---

## 2. MẢNG 1: Nhận Diện Người Dùng Tương Tác (Vision / Presence Detection)

*Thư mục lưu trữ thử nghiệm & tài liệu Backup:* [experiments/device_runtime/](file:///d:/work/project_company/kiosk/experiments/device_runtime)

Để Kiosk biết khi nào có người dân đến gần và chủ động bắt đầu cuộc hội thoại, hệ thống đã trải qua hai thử nghiệm nhận diện hình ảnh lớn:

### Thử nghiệm 1: Nhận diện dựa trên MediaPipe Tasks (`person_usage_device_test.py`)
*   **Mô hình sử dụng**: `pose_landmarker_lite.task` và `face_landmarker.task`.
*   **Nguyên lý hoạt động**: Phát hiện nhanh tư thế cơ thể (pose) và các điểm mốc khuôn mặt (face landmarks). Tính toán tỷ lệ chiều rộng vai và khoảng cách để xác định người dùng có đang đứng đối diện và trong khu vực hoạt động tích cực (Active Zone) của Kiosk hay không.
*   **Tài liệu chi tiết**: [EXPERIMENT_01_REVIEW.md](file:///d:/work/project_company/kiosk/experiments/device_runtime/EXPERIMENT_01_REVIEW.md) (Được lưu trữ nguyên vẹn để backup).

### Thử nghiệm 2: Nhận diện nâng cao Holistic (`holistic_usage_research.py`)
*   **Mô hình sử dụng**: MediaPipe Holistic Solution (Pose + Face + Iris Gaze Tracking).
*   **Nguyên lý hoạt động**: Nghiên cứu sâu hơn hướng nhìn của mắt (iris gaze) để biết chính xác người dân có đang thật sự nhìn vào màn hình Kiosk để giao tiếp hay không, đồng thời phân tích nét mặt để phát hiện trạng thái cảm xúc.
*   **Tài liệu chi tiết**: [EXPERIMENT_02_HOLISTIC_REVIEW.md](file:///d:/work/project_company/kiosk/experiments/device_runtime/EXPERIMENT_02_HOLISTIC_REVIEW.md) (Được lưu trữ nguyên vẹn để backup).

---

## 3. MẢNG 2: Voicebot & Giao Tiếp Ngôn Ngữ Tự Nhiên (Audio / STT)

*Thư mục lưu trữ thử nghiệm:* [experiments/realtime_voicebot_lab/](file:///d:/work/project_company/kiosk/experiments/realtime_voicebot_lab)

Mảng hội thoại giọng nói hiện tại đang ở **Giai đoạn 4 (Prototype Realtime Streaming)** và phần nhận dạng giọng nói (STT) đã được đánh giá là **hoàn thiện xuất sắc** với luồng hoạt động cụ thể:

### Luồng Hoạt Động & Truyền Nhận Thực Tế:
1.  **Kiosk (Thiết bị thu)**: Đóng vai trò capture thô. Kiosk kết nối và bật Microphone ghi âm giọng nói của người dân, đóng gói dữ liệu âm thanh dưới dạng các gói tin nhị phân đặc thù và truyền liên tục qua cáp Ethernet/LAN sang Laptop bằng WebSocket.
2.  **Laptop (Máy tính chính - Thiết bị xử lý)**: 
    *   **Laptop không mở Microphone cục bộ**, chỉ mở cổng WebSocket để nhận luồng âm thanh nhị phân từ Kiosk gửi sang.
    *   Đưa dữ liệu vào mô hình **STT Zipformer tiếng Việt** chạy offline để giải mã thành văn bản.
3.  **Cách thức hiển thị**: 
    *   Văn bản nhận diện xong được **in trực tiếp lên terminal của Laptop** dưới dạng **Final text hoàn chỉnh** (khi người dùng dứt câu).
    *   Chữ được in nối tiếp nhau thành một đoạn văn viết liên tục, cập nhật mượt mà và sinh động y hệt video demo của repo `RealtimeSTT` để người giám sát tại Laptop có thể theo dõi trọn vẹn nội dung hội thoại.

---

## 4. Trạng Thế Hiện Tại & Các Bước Tiếp Theo

Dự án đang tập trung triển khai **Giai đoạn 4 (Realtime Streaming)**:
*   `[x]` Thiết lập kết nối mạng LAN Ethernet ổn định giữa Kiosk và Laptop (RTT cực thấp ~0.5ms).
*   `[x]` Hoàn thiện luồng truyền dữ liệu âm thanh nhị phân thô từ mic Kiosk sang Laptop.
*   `[x]` Hoàn thiện module STT Zipformer giải mã và in chữ nối tiếp lên terminal Laptop.
*   `[ ]` **Bước tiếp theo**: Tích hợp mô hình ngôn ngữ lớn **LLM RAG** trên Laptop để sinh câu trả lời dạng stream (SSE - Server-Sent Events).
*   `[ ]` **Bước tiếp theo**: Nghiên cứu và thử nghiệm quy trình phát loa trả lời bằng Windows TTS local trên Kiosk sau khi phần LLM hoàn tất.
