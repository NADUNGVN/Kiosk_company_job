# Bối Cảnh Nghiên Cứu: Từ Cảm Biến Hồng Ngoại Đến Computer Vision Cho Kiosk

## 1. Vấn Đề Nghiên Cứu

Hệ thống kiosk trước đây sử dụng cảm biến hồng ngoại/RS485 để xác định phía
trước thiết bị có người hay không. Cách tiếp cận này có ưu điểm là đơn giản,
chi phí tính toán thấp và phản hồi nhanh. Tuy nhiên, tín hiệu cảm biến chỉ cho
biết trạng thái nhị phân: có người hoặc không có người.

Trong ngữ cảnh kiosk hành chính công, trạng thái nhị phân này chưa đủ để quyết
định khi nào nên kích hoạt giao tiếp. Một người có thể đi ngang qua, đứng gần
nhưng không có nhu cầu, đang nhìn sang hướng khác, hoặc thật sự đang cần hỗ trợ.
Các tình huống này có cùng tín hiệu “có người” với cảm biến hồng ngoại, nhưng
yêu cầu phản hồi hệ thống khác nhau.

Vì vậy, hướng phát triển hiện tại chuyển sang **computer vision** nhằm ước lượng
ngữ cảnh hành vi của khách hàng, thay vì chỉ phát hiện sự hiện diện vật lý.

## 2. Hạn Chế Của Cảm Biến Hồng Ngoại/RS485

Trong mã hiện tại, `core.hardware.rs485.RS485Sensor` đọc tín hiệu:

- `$0001#`: người tiến vào vùng cảm biến.
- `$0000#`: người rời vùng cảm biến.

Callback mặc định phát âm thanh:

- Khi có người: “Chào bạn”.
- Khi người rời đi: “Tạm biệt”.

Các hạn chế chính:

- Không xác định được người có đang nhìn vào kiosk hay không.
- Không phân biệt được người đi ngang với người thật sự cần hỗ trợ.
- Không đánh giá được hướng cơ thể, hướng mặt, mắt hoặc hành vi tương tác.
- Không tạo được trạng thái phiên giao tiếp bền vững như `SESSION_OPEN`,
  `SESSION_CLOSING`, hoặc `NEED_SUPPORT`.
- Có nguy cơ kích hoạt chatbot sai thời điểm, làm trải nghiệm kiosk bị nhiễu.

## 3. Chatbot Hiện Tại Trong Hệ Thống

Chatbot hiện tại thuộc app `backend.voice_chatbot`. Về bản chất, đây là chatbot
thoại theo luật và từ khóa, chưa phải mô hình hội thoại ngữ nghĩa sâu.

Các thành phần chính:

- `Keyword`: tập từ khóa gắn với từng quầy/dịch vụ.
- `ConversationLog`: lưu input của người dùng và phản hồi của bot.
- `process_request`: nhận `speech_text`, so khớp keyword, sinh phản hồi và trả
  về `audio_url`.
- `gTTS`: tạo file âm thanh tiếng Việt cho phản hồi.
- `speech_recognition`: dùng trong một số luồng để nhận dạng giọng nói tiếng
  Việt qua Google Speech Recognition.

Luồng xử lý cơ bản:

1. Người dùng nói yêu cầu.
2. Hệ thống chuyển giọng nói thành văn bản.
3. Văn bản được so khớp với danh sách `Keyword`.
4. Nếu khớp, bot hướng dẫn người dùng chọn quầy/dịch vụ tương ứng.
5. Nếu không khớp, bot hướng dẫn liên hệ cán bộ.
6. Phản hồi được chuyển thành âm thanh bằng gTTS.
7. Hội thoại được ghi vào `ConversationLog`.

Vì chatbot hiện tại phụ thuộc nhiều vào thời điểm kích hoạt và chất lượng input,
computer vision cần đóng vai trò như một lớp **gating** phía trước: chỉ mở giao
tiếp khi có bằng chứng khách hàng thật sự đang cần hỗ trợ.

## 4. Vai Trò Của Computer Vision

Computer vision không thay thế chatbot. Nhiệm vụ của nó là quyết định **khi nào
nên bắt đầu hoặc duy trì một phiên giao tiếp**.

Các tín hiệu thị giác cần quan sát:

- Có người trong khung hình hay không.
- Người có ở vùng gần kiosk hay không.
- Người có đứng lại hay chỉ đi ngang.
- Vai/thân người có hướng về kiosk hay không.
- Mặt có quay về phía kiosk/camera hay không.
- Mắt/iris có gợi ý người đang chú ý vào máy hay không.
- Tín hiệu có ổn định đủ lâu để mở hội thoại hay không.

Do đó, mục tiêu nghiên cứu không phải là nhận diện danh tính khách hàng, mà là
ước lượng trạng thái tương tác:

- `NO_PERSON`
- `PASSING_BY`
- `PERSON_PRESENT_NOT_ATTENDING`
- `ATTENTION_CANDIDATE`
- `NEED_SUPPORT`
- `SESSION_OPEN`
- `SESSION_CLOSING`

## 5. Các Issue Nghiên Cứu Chung

### Issue 1: Kích Hoạt Sai Do Tín Hiệu Hiện Diện Đơn Giản

Nếu chỉ dùng cảm biến hồng ngoại hoặc chỉ dùng `person_present`, hệ thống dễ
kích hoạt khi người đi ngang qua. Điều này làm chatbot mở không đúng nhu cầu,
tạo cảm giác bị làm phiền và làm giảm độ tin cậy của kiosk.

### Issue 2: Thiếu Trạng Thái Phiên Giao Tiếp

Một hệ thống giao tiếp không chỉ cần biết lúc nào mở, mà còn cần biết lúc nào
duy trì, tạm ngưng hoặc đóng phiên. Hai thử nghiệm hiện tại mới tập trung vào
kích hoạt ban đầu, chưa hoàn thiện vòng đời phiên.

### Issue 3: Thiếu Smoothing Cho Tín Hiệu Thị Giác

Pose, face và gaze có thể mất tạm thời do ánh sáng, góc quay, chuyển động hoặc
che khuất. Nếu rule reset ngay khi mất tín hiệu trong một vài frame, trạng thái
sẽ nhấp nháy và làm chatbot phản hồi thiếu ổn định.

### Issue 4: Chưa Có Đủ Kịch Bản Âm Tính

Các video hiện tại đã cho thấy hướng phát hiện người cần hỗ trợ, nhưng cần thêm
video âm tính như người đi ngang nhanh, đứng gần nhưng dùng điện thoại, quay
mặt sang hướng khác, hoặc đứng trong phòng nhưng không sử dụng kiosk.

### Issue 5: Gắn Kết Vision Với Chatbot Chưa Hoàn Chỉnh

Hiện tại thử nghiệm vision chỉ mock việc mở voicebot. Giai đoạn tiếp theo cần
thiết kế rõ interface giữa vision và chatbot, ví dụ:

- `NEED_SUPPORT`: phát lời chào và bắt đầu lắng nghe.
- `PERSON_PRESENT_NOT_ATTENDING`: chỉ hiển thị gợi ý nhẹ, chưa phát thoại.
- `PASSING_BY`: không phản hồi.
- `SESSION_CLOSING`: kết thúc hoặc tạm dừng lắng nghe.

## 6. Hướng Phát Triển Đề Xuất

Hướng phát triển nên đi theo kiến trúc hai lớp:

- Lớp nhận thức ngữ cảnh bằng computer vision: xác định trạng thái hành vi của
  khách hàng.
- Lớp hội thoại: sử dụng trạng thái đó để quyết định mở, duy trì hoặc đóng
  chatbot.

Trong ngắn hạn, nên ưu tiên:

- Hoàn thiện state machine cho phiên giao tiếp.
- Thêm activation hold và deactivation hold.
- Thêm movement filter để nhận diện người đi ngang.
- Thu thêm video âm tính theo kịch bản có kiểm soát.
- Chuẩn hóa log để so sánh được giữa các phương án MediaPipe Tasks và Holistic.
