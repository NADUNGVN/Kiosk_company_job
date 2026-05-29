# Hướng Dẫn Vận Hành & Kịch Bản Đánh Giá STT Thực Tế (LAN)

Tài liệu này hướng dẫn nhanh cách chạy thử nghiệm và cung cấp kịch bản đo đạc thông số thực tế khi stream giọng nói từ Microphone Kiosk sang Laptop.

---

## 1. Hướng Dẫn Chạy Nhanh (How To Run)

### BƯỚC 1: Khởi chạy trên Laptop (`192.168.1.234`)
Mở terminal trên Laptop và chạy lệnh mở Server STT trên cổng `8012`:
```powershell
cd D:\work\project_company\kiosk\experiments\realtime_voicebot_lab\stt_zipformer_vi_server
.\.venv\Scripts\python.exe .\backend_server.py --host 0.0.0.0 --port 8012
```
*(Đợi dòng: `Uvicorn running on http://0.0.0.0:8012` xuất hiện)*

### BƯỚC 2: Khởi chạy trên Kiosk (`192.168.1.169`)
Cắm Micro vào Kiosk, mở terminal và chạy lệnh kết nối truyền âm thanh trực tiếp:
```powershell
python experiments\realtime_voicebot_lab\kiosk_laptop_conn_test\client_test.py --server ws://192.168.1.234:8012/ws/transcribe --mode stt --source mic
```
*(Khi Kiosk hiển thị `Microphone đang BẬT!`, bạn bắt đầu đọc kịch bản bên dưới)*

---

## 2. Kịch Bản Đọc Thử Nghiệm & Bảng Ghi Nhận Thông Số

Bạn hãy đọc to, rõ ràng từng câu dưới đây vào Micro của Kiosk, sau đó quan sát **chữ hiển thị trên terminal của Laptop** và ghi nhận lại các thông số vào bảng mẫu bên dưới để đánh giá thực tế.

### Tập câu đọc thử nghiệm:
1.  **Câu ngắn (Chào hỏi)**: *"Xin chào máy tính."*
2.  **Câu trung bình (Hỏi dịch vụ công)**: *"Tôi muốn làm thẻ căn cước công dân ở đâu?"*
3.  **Câu dài (Hội thoại phức tạp)**: *"Cho tôi hỏi thủ tục đăng ký khai sinh cho trẻ em trực tuyến cần những giấy tờ gì?"*
4.  **Câu đọc nhanh (Kiểm tra tốc độ ASR)**: *"Cảm ơn bạn đã hỗ trợ tôi nhiệt tình ngày hôm nay."*

---

### Mẫu Bảng Ghi Nhận Thông Số Đánh Giá (Copy để ghi chép):

| STT | Câu đọc thực tế (Expected) | Chữ nhận dạng trên Laptop (Actual) | Độ chính xác (Khớp 100% / Sai từ / Lỗi) | Độ trễ cảm giác (Tức thì / Hơi trễ / Chậm) |
|---|---|---|---|---|
| 1 | Xin chào máy tính. | | | |
| 2 | Tôi muốn làm thẻ căn cước công dân ở đâu? | | | |
| 3 | Cho tôi hỏi thủ tục đăng ký khai sinh... | | | |
| 4 | Cảm ơn bạn đã hỗ trợ tôi nhiệt tình... | | | |

*Ghi chú về Độ trễ cảm giác:*
*   **Tức thì**: Dưới 0.5 giây kể từ khi dứt lời là chữ xuất hiện hoàn chỉnh.
*   **Hơi trễ**: Từ 0.5s đến 1.5 giây.
*   **Chậm**: Trên 1.5 giây.
