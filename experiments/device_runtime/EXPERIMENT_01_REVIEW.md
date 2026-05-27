# Đánh Giá Thử Nghiệm 01: Runtime Nhận Diện Người Sử Dụng Kiosk

## Bối Cảnh Và Công Nghệ Được Dùng

Thử nghiệm này kiểm tra runtime nhận diện người đang sử dụng kiosk bằng webcam
trên thiết bị thật.

Về mặt nghiên cứu, thử nghiệm này nằm trong quá trình chuyển từ cơ chế kích hoạt
dựa trên cảm biến hồng ngoại/RS485 sang cơ chế nhận thức ngữ cảnh bằng computer
vision. Cảm biến hồng ngoại trước đây chỉ xác định có người ở phía trước thiết
bị, trong khi mục tiêu mới là xác định người đó có thật sự đang cần tương tác
với kiosk hay không.

- Mã runtime: `person_usage_device_test.py`
- Thư mục kết quả: `outputs/device_usage_tests/20260526_142623`
- Camera: `0`
- Thời lượng mục tiêu: `60.0` giây
- Thời lượng thực tế: `50.078` giây, dừng bằng `q_or_escape`
- Số frame xử lý: `498`
- FPS xử lý trung bình: `9.94`
- Latency trung bình: `84.14 ms/frame`
- RAM trung bình: `219.66 MB`

Thử nghiệm này dùng **MediaPipe Tasks Vision**, không dùng Holistic:

- `PoseLandmarker` với model `pose_landmarker_lite.task`
- `FaceLandmarker` với model `face_landmarker.task`
- Webcam input trực tiếp từ OpenCV
- Voicebot chưa được tích hợp thật, chỉ mock bằng event `voicebot_mock_opened`

Logic hiện tại là **rule-based**, không train model:

- `person_present`: có pose hoặc face.
- `active_zone`: chủ yếu dựa trên kích thước vai từ pose; nếu không có pose thì
  dùng kích thước mặt.
- `attention`: chỉ đúng khi có người, đang trong active zone, có pose, vai hướng
  về camera, có face, head facing, và thấy mắt.
- `greeting_triggered`: xảy ra khi `attention` giữ liên tục đủ `usage_hold_sec`.
- `usage_hold_sec` trong thử nghiệm này: `3.0` giây.

Trong hệ thống hiện tại, chatbot thoại thuộc app `backend.voice_chatbot` vẫn là
chatbot theo keyword: nhận `speech_text`, so khớp `Keyword` theo quầy/dịch vụ,
tạo phản hồi bằng gTTS và ghi `ConversationLog`. Vì vậy, computer vision ở thử
nghiệm này chưa thay thế chatbot, mà đóng vai trò lớp kích hoạt trước hội thoại:
chỉ nên mở voicebot khi có đủ bằng chứng người dùng đang chú ý và cần hỗ trợ.

## File Kết Quả

Lần pull dữ liệu mới đã có đầy đủ file để đánh giá:

- `raw.mp4`: video gốc.
- `annotated.mp4`: video có overlay debug.
- `config.json`: cấu hình runtime khi chạy.
- `metrics.csv`: số liệu tổng hợp.
- `frame_metrics.csv`: mẫu trạng thái theo từng giây.
- `events.csv`: các event chuyển trạng thái.
- `summary.md`: summary tự sinh từ runtime.

## Kết Quả Định Lượng

Các mốc quan trọng từ `metrics.csv` và `events.csv`:

- `active_zone_entered` đầu tiên tại `5.371s`.
- `attention_started` đầu tiên tại `7.429s`, nhưng mất nhanh tại `7.619s`.
- `attention_started` lại tại `7.804s`.
- `greeting_triggered` tại `10.82s`, tức là attention giữ đủ `3.0s`.
- `voicebot_mock_opened` cũng tại `10.82s`.
- Tổng số frame active zone: `298 / 498`.
- Tổng số frame attention: `160 / 498`.

Nhận xét:

- Đoạn đầu khi người còn xa được đánh đúng là `TOO_FAR`.
- Khi người tiến gần và nhìn vào kiosk, hệ thống chuyển `ACTIVE`, sau đó chuyển
  `attention True`, rồi trigger sau khi giữ đủ 3 giây. Đây là hành vi đúng cho
  tình huống người thật sự cần hỗ trợ.
- Sau khi trigger, `voicebot_mock_opened` giữ `True` đến cuối video, kể cả khi
  người rời active zone hoặc mất attention. Đây là điểm cần sửa nếu runtime muốn
  mô phỏng vòng đời phiên giao tiếp thật.
- Sau mốc `18s`, attention bị mất và bật lại nhiều lần. Điều này cho thấy rule
  đang nhạy với thay đổi pose/face khi người di chuyển qua lại.

## Đánh Giá Rule Hiện Tại

Rule hiện tại dùng được để chứng minh hướng tiếp cận khả thi:

- Nhận được người ở xa nhưng không kích hoạt.
- Nhận được người ở gần, nhìn vào máy, và trigger sau thời gian chờ.
- Có log đủ để phân tích lại theo event và frame sample.

Tuy nhiên rule chưa đủ chắc cho các tình huống đi ngang hoặc rời vùng:

1. Chưa có reset/deactivate sau khi mock voicebot mở. Khi mất `attention` liên
   tục 1-2 giây, hệ thống nên ghi `voicebot_closed` hoặc chuyển về trạng thái
   chờ mới.
2. `attention_lost` đang ghi detail `countdown_reset_at_0.00s`, do countdown đã
   bị reset trước khi ghi event. Nên log giá trị countdown trước khi reset để
   biết lần attention đó kéo dài bao lâu.
3. Active zone hiện vẫn dựa nhiều vào kích thước vai/mặt. Với không gian thử
   nghiệm này, về sau nên thêm vùng vị trí gần kiosk để giảm false-positive từ
   người đi ngang trong phòng.
4. Người di chuyển qua lại làm trạng thái `attention` bật/tắt nhiều lần. Cần
   thêm smoothing hoặc state machine rõ hơn để tránh nhấp nháy.
5. Chưa có kiểm tra tốc độ di chuyển. Người đi ngang thường có tâm vai/tâm người
   thay đổi nhanh; yếu tố này nên dùng để phân biệt `PASSING_BY` với người thật
   sự đứng dùng kiosk.

## Issues Của Thử Nghiệm 01

### Issue 01: Tín Hiệu Presence Chưa Đủ Cho Bài Toán Hội Thoại

Thử nghiệm đã vượt qua giới hạn cơ bản của cảm biến hồng ngoại bằng cách dùng
pose và face, nhưng rule vẫn có lớp `person_present` khá rộng. Nếu tín hiệu này
được dùng trực tiếp để mở chatbot, hệ thống vẫn có nguy cơ phản hồi với người
chỉ xuất hiện trong khung hình nhưng chưa có ý định sử dụng máy.

Ảnh hưởng: chatbot có thể phát lời chào hoặc bắt đầu lắng nghe sai thời điểm,
làm nhiễu trải nghiệm người dùng.

### Issue 02: Chưa Có Vòng Đời Phiên Giao Tiếp

Sự kiện `voicebot_mock_opened` được bật tại `10.82s`, nhưng sau đó không có cơ
chế đóng phiên khi người dùng rời attention hoặc rời active zone. Đây là vấn đề
quan trọng vì chatbot thực tế cần biết khi nào bắt đầu, duy trì và kết thúc hội
thoại.

Ảnh hưởng: nếu tích hợp trực tiếp với chatbot hiện tại, phiên thoại có thể bị
giữ mở quá lâu hoặc tiếp tục lắng nghe khi người dùng đã rời đi.

### Issue 03: Rule Attention Bị Nhạy Với Mất Face/Head Tạm Thời

Sau mốc `18s`, event cho thấy `attention_started` và `attention_lost` xuất hiện
nhiều lần. Điều này phản ánh việc rule phụ thuộc trực tiếp vào pose/face từng
frame, chưa có smoothing theo thời gian.

Ảnh hưởng: chatbot có thể bị kích hoạt/ngắt logic nội bộ không ổn định nếu trạng
thái attention được dùng trực tiếp làm tín hiệu điều khiển.

### Issue 04: Thiếu Phân Loại Hành Vi Âm Tính

Thử nghiệm 01 chứng minh được trường hợp người tiến gần và nhìn vào kiosk, nhưng
chưa đủ để kết luận hệ thống tránh được các ca âm tính như đi ngang nhanh, đứng
gần nhưng dùng điện thoại, hoặc đứng trong phòng nhưng không cần hỗ trợ.

Ảnh hưởng: chưa đánh giá được false-positive trong điều kiện vận hành thực tế.

### Issue 05: Interface Với Chatbot Mới Dừng Ở Mock

Runtime mới ghi event `voicebot_mock_opened`, chưa gọi trực tiếp luồng chatbot.
Trong khi đó chatbot hiện tại cần input thoại (`speech_text`) và phản hồi bằng
TTS. Do đó cần thiết kế interface trung gian rõ ràng giữa vision state và vòng
đời hội thoại.

Ảnh hưởng: chưa thể đảm bảo rằng trigger từ vision sẽ phối hợp đúng với các
trạng thái nghe, nói, kết thúc và ghi log của chatbot.

## Đề Xuất Hướng Phát Triển

Hướng cải thiện nên đi theo state machine rõ ràng hơn:

- `NO_PERSON`: không có người.
- `PERSON_FAR`: có người nhưng ở xa hoặc ngoài vùng hỗ trợ.
- `PASSING_BY`: có người nhưng di chuyển nhanh, không giữ attention đủ lâu.
- `PERSON_PRESENT_NOT_ATTENDING`: có người gần kiosk nhưng chưa nhìn/quan tâm.
- `ATTENTION_CANDIDATE`: đủ điều kiện attention và đang đếm thời gian.
- `NEED_SUPPORT`: attention giữ đủ thời gian, có thể mở greeting/voicebot.
- `SESSION_OPEN`: đã mở voicebot mock hoặc phiên giao tiếp.
- `SESSION_CLOSING`: mất attention liên tục đủ lâu, chuẩn bị đóng phiên.

Các rule nên thêm ở bước sau:

- Activation hold: chỉ mở khi `ATTENTION_CANDIDATE` giữ đủ 2-3 giây.
- Deactivation hold: chỉ đóng khi mất attention liên tục 1-2 giây.
- Movement filter: nếu body center di chuyển nhanh thì ưu tiên `PASSING_BY`.
- Face/eye smoothing: cho phép mất mặt/mắt rất ngắn nhưng không cho mất lâu.
- Gaze debug: giữ head axis ở mặt và thêm vector mắt từ `eye_center` đến
  `iris_center`; không nên hiểu vector mắt này là gaze tuyệt đối chính xác.

## Kết Luận

Thử nghiệm 01 cho thấy hướng MediaPipe Tasks `PoseLandmarker + FaceLandmarker`
có thể phát hiện đúng trường hợp người tiến gần kiosk và nhìn vào máy. Trigger
tại `10.82s` là hợp lý với cấu hình giữ attention `3.0s`.

Điểm cần cải thiện lớn nhất không phải model, mà là logic phiên và rule ổn định
trạng thái: cần phân biệt rõ người đi ngang, người đứng gần nhưng không cần hỗ
trợ, người thật sự cần hỗ trợ, và trạng thái đóng/mở phiên voicebot.
