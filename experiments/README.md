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
    *   Xử lý suy nghĩ, tra cứu cơ sở dữ liệu tri thức **LLM RAG** (Ollama Qwen) và trả về kết quả.

---

## 2. MẢNG 1: Nhận Diện Người Dùng Tương Tác (Vision / Presence Detection)

*Thư mục lưu trữ thử nghiệm & tài liệu Backup:* [experiments/device_runtime/](file:///d:/work/project_company/kiosk/experiments/device_runtime)

Để Kiosk biết khi nào có người dân đến gần và chủ động mở lời chào, hệ thống đã trải qua 2 thử nghiệm lớn dùng Computer Vision thay thế cho cảm biến hồng ngoại thụ động:

### Thử nghiệm 01: Nhận diện dựa trên MediaPipe Tasks
*   **Mã nguồn vận hành**: [person_usage_device_test.py](file:///d:/work/project_company/kiosk/experiments/device_runtime/person_usage_device_test.py)
*   **Cách thức vận hành**: 
    1. Thiết lập camera góc rộng của Kiosk kết nối với script Python.
    2. Sử dụng hai luồng mô hình song song `pose_landmarker_lite.task` và `face_landmarker.task`.
    3. Trích xuất khoảng cách vai và diện tích khuôn mặt của người đối diện, tính toán theo bộ quy tắc toán học (rule-based) để lọc ra khoảng cách thích hợp (`Active Zone`).
    4. Giám sát thời gian giữ sự chú ý (`usage_hold_sec = 3.0s`) để kích hoạt hội thoại ảo.
*   **Kết quả vận hành thực tế & Chỉ số đạt được**:
    *   **Tốc độ xử lý (FPS)**: ~`9.94 FPS` (Rất mượt mà trên phần cứng kiosk).
    *   **Độ trễ trung bình (Latency)**: ~`84.14 ms/frame`.
    *   **Tài nguyên tiêu thụ (RAM)**: ~`219.66 MB`.
    *   **Trạng thái hoạt động**:
        *   Khi người dùng ở xa (>2m): Hệ thống báo trạng thái `TOO_FAR` và không kích hoạt lời chào nhầm.
        *   Khi người dùng đứng đối diện Kiosk: Trạng thái chuyển sang `ACTIVE` và bắt đầu đếm ngược 3 giây.
        *   Kích hoạt lời chào thành công: Tại mốc `10.82 giây`, sự kiện `voicebot_mock_opened` được kích hoạt hoàn toàn chính xác.
*   **Tài liệu chi tiết**: [EXPERIMENT_01_REVIEW.md](file:///d:/work/project_company/kiosk/experiments/device_runtime/EXPERIMENT_01_REVIEW.md)

### Thử nghiệm 02: Nhận diện nâng cao bằng Holistic (Iris Gaze & Emotional Landmarks)
*   **Mã nguồn vận hành**: [holistic_usage_research.py](file:///d:/work/project_company/kiosk/experiments/device_runtime/holistic_usage_research.py)
*   **Cách thức vận hành**:
    1. Chạy API tích hợp `mediapipe.python.solutions.holistic.Holistic`.
    2. Theo dõi đồng thời Pose (Tư thế cơ thể), Face (Điểm mốc khuôn mặt) và đặc biệt là Iris Gaze (Hướng nhìn của mắt).
    3. Tính toán độ lệch tâm của con ngươi so với hốc mắt (`gaze_centered`) và vận tốc di chuyển của người để phát hiện người đi ngang qua (`PASSING_BY`).
*   **Kết quả vận hành thực tế & Chỉ số đạt được**:
    *   **Tốc độ xử lý (FPS)**: ~`9.17 FPS`.
    *   **Độ trễ trung bình (Latency)**: ~`90.13 ms/frame`.
    *   **Tài nguyên tiêu thụ (RAM)**: ~`639.83 MB` (Tốn bộ nhớ gấp gần 3 lần so với Tasks).
    *   **Trạng thái hoạt động**:
        *   Phát hiện người ở xa chính xác ban đầu là `TOO_FAR`.
        *   Chuyển trạng thái `POTENTIAL_USER` tại mốc `8.506s` khi người dùng di chuyển chậm lại và nhìn thẳng màn hình.
        *   Nhận diện nhu cầu hỗ trợ thực tế (`NEED_SUPPORT`) thành công tại mốc `11.398s` sau khi duy trì con mắt nhìn trực diện đủ 3 giây.
*   **Tài liệu chi tiết**: [EXPERIMENT_02_HOLISTIC_REVIEW.md](file:///d:/work/project_company/kiosk/experiments/device_runtime/EXPERIMENT_02_HOLISTIC_REVIEW.md)

---

## 3. MẢNG 2: Voicebot & Giao Tiếp Ngôn Ngữ Tự Nhiên (Audio / STT / LLM)

*Thư mục lưu trữ thử nghiệm:* [experiments/realtime_voicebot_lab/](file:///d:/work/project_company/kiosk/experiments/realtime_voicebot_lab)

Mảng hội thoại thông minh đang ở **Giai đoạn 4 (Prototype Realtime Streaming)** với việc tích hợp thành công hai cấu phần cực kỳ quan trọng: Luồng âm thanh nhị phân thời gian thực LAN và Kênh suy nghĩ thông minh LLM local.

### Giai đoạn 4.1: Thử nghiệm kết nối mạng LAN & Truyền âm thanh nhị phân thô
*   **Mã nguồn vận hành**: 
    *   Server Echo Laptop: `server_echo.py` (Cổng `8012`)
    *   Client Kiosk: [client_test.py](file:///d:/work/project_company/kiosk/experiments/realtime_voicebot_lab/kiosk_laptop_conn_test/client_test.py)
*   **Cách thức vận hành**:
    1. Laptop và Kiosk cùng kết nối chung một mạng LAN nội bộ.
    2. Client trên Kiosk mở luồng ghi âm thô từ Microphone hoặc file WAV chuẩn `16kHz, mono, s16le`.
    3. Đóng gói luồng byte âm thanh theo định dạng gói tin đặc thù của server: `[4B json_len][Metadata JSON][PCM raw]` và đẩy liên tiếp qua kết nối WebSocket LAN sang Laptop.
*   **Kết quả vận hành thực tế & Chỉ số đạt được**:
    *   **Độ trễ mạng LAN (RTT)**: Cực kì thấp, trung bình chỉ đạt **`0.5ms đến 2ms`**, đảm bảo truyền dẫn ngay tức thì.
    *   **Tính toàn vẹn của âm thanh**: File WAV nhận được trên Laptop nghe cực kỳ mượt mà, không bị vấp tiếng, không mất gói tin nhờ cơ chế TCP WebSocket truyền tin ổn định.

### Giai đoạn 4.2: Tích hợp STT Zipformer Tiếng Việt & Local LLM (Qwen qua Ollama)
*   **Mã nguồn vận hành**:
    *   Server STT + LLM Laptop: [server.py](file:///d:/work/project_company/kiosk/experiments/realtime_voicebot_lab/stt_zipformer_vi_server/server_app/server.py) (Cổng `8012`)
    *   Client Kiosk: [client_test.py](file:///d:/work/project_company/kiosk/experiments/realtime_voicebot_lab/kiosk_laptop_conn_test/client_test.py) (Gọi WebSocket STT)
*   **Cách thức vận hành**:
    1. Khởi động dịch vụ Ollama local trên Laptop và kéo model `qwen3:4b` (hoặc Qwen bất kỳ).
    2. Khởi chạy Server STT. Khi người dùng nói qua Microphone của Kiosk, dữ liệu truyền sang Laptop sẽ được giải mã trực tiếp bằng mô hình Zipformer tiếng Việt chạy offline.
    3. Khi người dùng dứt lời phát biểu (VAD chốt câu), server tự động chạy bộ lọc Regex thông minh (`re.sub`) để làm sạch các lỗi lặp âm đuôi (như `đâu.âu`, `gì.gì`) đặc trưng của VAD.
    4. Gửi câu hỏi đã làm sạch vào local Ollama qua cơ chế streaming. Laptop sẽ in trực tiếp từng chữ ra màn hình terminal trong thời gian thực để phục vụ giám sát, sau đó gom toàn bộ câu trả lời hoàn chỉnh để gửi ngược về Kiosk qua WebSocket.
*   **Kết quả vận hành thực tế & Chỉ số đạt được**:
    *   **Độ chính xác nhận diện giọng nói (STT)**: Rất cao, nhận dạng rõ từng từ tiếng Việt có dấu, kể cả các câu hỏi dài phức tạp về hành chính dịch vụ công.
    *   **Xử lý lặp âm đuôi**: Đã xử lý triệt để, đầu vào đưa vào LLM hoàn toàn chuẩn hóa.
    *   **Tốc độ sinh chữ LLM**: Phản hồi tức thì ngay sau khi dứt câu nhờ model Qwen gọn nhẹ chạy trực tiếp trên GPU Laptop, thời gian trễ phản hồi cảm giác cực ngắn.

---

## 4. TẤT CẢ CÁC GIAI ĐOẠN ĐÃ THỬ NGHIỆM VÀ KẾT QUẢ ĐẠT ĐƯỢC

Dưới đây là bảng tổng hợp trực quan về tiến trình thử nghiệm dự án để phục vụ báo cáo và vận hành:

| Giai Đoạn Thử Nghiệm | Mục Tiêu & Kịch Bản Kiểm Thử | Cách Thức Vận Hành Thực Tế | Kết Quả Đạt Được & Thông Số Kỹ Thuật | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| **Giai Đoạn 1: Vision - MediaPipe Tasks** | Nhận diện sự hiện diện của người dùng đối diện Kiosk để kích hoạt lời chào thông minh. | Chạy script `person_usage_device_test.py` trên Kiosk, bắt luồng Camera vật lý. | - Xử lý đạt **9.94 FPS**, trễ chỉ **84.14ms/frame**.<br>- RAM nhẹ: **219.66 MB**.<br>- Nhận diện người ở xa/gần cực chuẩn, kích hoạt lời chào chào mừng sau 3 giây giữ attention (mốc 10.82s). | **Hoàn Thành** |
| **Giai Đoạn 2: Vision - MediaPipe Holistic** | Nghiên cứu sâu hành vi hướng nhìn (Iris Gaze) để tăng độ chính xác chú ý của người dùng. | Chạy script `holistic_usage_research.py` trên Kiosk với thuật toán Iris Gaze tracking. | - Xử lý đạt **9.17 FPS**, trễ **90.13ms/frame**.<br>- RAM nặng: **639.83 MB**.<br>- Cho phép phân tích chính xác hướng mắt nhìn thẳng vào Kiosk, kích hoạt `NEED_SUPPORT` ở mốc 11.398s. | **Hoàn Thành** |
| **Giai Đoạn 3: Voicebot - LAN Connection** | Kiểm thử đường truyền âm thanh nhị phân tốc độ cao Kiosk $\rightarrow$ Laptop qua LAN Ethernet. | Chạy Server Echo trên Laptop (cổng 8012), chạy Client `client_test.py` trên Kiosk để stream mic/WAV. | - RTT mạng LAN siêu tốc: **0.5ms - 2ms**.<br>- Truyền âm thanh nhị phân thô trọn vẹn 100%, không bị vấp hay mất gói tin. | **Hoàn Thành** |
| **Giai Đoạn 4: Voicebot - STT + Local LLM** | Giải mã giọng nói tiếng Việt bằng Zipformer và sinh câu trả lời trực tiếp bằng Qwen2.5:7B thông qua Ollama. | **Laptop**: Chạy Server STT Zipformer kết nối với API Ollama local, tối ưu hóa triệt tiêu lỗi tiếng Trung.<br>**Kiosk**: Stream âm thanh Microphone trực tiếp qua WebSocket. | - Nhận diện STT tiếng Việt rõ ràng, lọc sạch lặp từ ở đuôi.<br>- LLM Qwen2.5:7B phản hồi siêu tốc, trả từ cực mượt.<br>- Giao diện sạch sẽ 100%, không bị rác chữ tiếng Trung. | **Hoàn Thành** |
| **Giai Đoạn 5: Voicebot - Laptop TTS Integration** | Tích hợp Windows WinRT TTS phát loa trực tiếp tại Laptop, áp dụng cơ chế gom câu (Sentence Buffering) & ngắt lời chủ động (Active Interruption) với giọng đọc **Microsoft An** chất lượng cao. | **Laptop**: Server STT giải mã văn bản, chạy bộ lọc ký tự tiếng Trung programmatically, truyền từng token đã lọc vào bộ đệm câu và đẩy vào hàng đợi WinRT TTS để phát âm thanh không chặn (SND_ASYNC).<br>Khi người dùng nói câu hỏi mới (STT FINAL), loa phát lập tức ngắt ngay và dọn dẹp bộ nhớ đệm mà không làm chết tiểu trình TTS (sử dụng cờ thread-safety và `self._is_active`). | - Giọng đọc **Microsoft An** Tiếng Việt phát cực kỳ tự nhiên và ổn định thông qua thư viện `winsdk`.<br>- Cơ chế cướp lời (Active Interruption) hoạt động hoàn hảo: khi người dùng ngắt lời, âm thanh dừng ngay lập tức và sẵn sàng phát câu mới mà không bị lỗi treo hay chết luồng.<br>- Bộ lọc tiếng Trung Regex tự động loại bỏ triệt để các rác ký tự Trung Quốc hoặc dấu câu full-width từ Qwen trước khi in hoặc phát âm thanh. | **Hoàn Thành** |

---

## 5. Hướng Dẫn Chạy Thử Nghiệm Giai Đoạn 4 (STT + LLM)

Để thực hiện chạy thử nghiệm liên kết và kiểm tra toàn bộ luồng từ lúc nói tại Kiosk đến khi LLM trả lời trên Laptop, vui lòng xem hướng dẫn chi tiết tại file tài liệu:
👉 **[Hướng Dẫn Vận Hành & Kịch Bản Đọc Thử Nghiệm](file:///d:/work/project_company/kiosk/experiments/realtime_voicebot_lab/kiosk_laptop_conn_test/HOW_TO_RUN.md)**

*Tài liệu này bao gồm kịch bản 4 câu đọc thử nghiệm tiếng Việt tiêu chuẩn cùng bảng ghi nhận thông số thực tế để đánh giá KPI hệ thống.*
