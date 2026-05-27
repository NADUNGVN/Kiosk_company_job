# Đánh Giá Thử Nghiệm 02: MediaPipe Holistic Research

## Bối Cảnh Và Công Nghệ Được Dùng

Thử nghiệm này kiểm tra hướng dùng **MediaPipe Holistic legacy** để nghiên cứu
logic nhận diện người đang sử dụng kiosk.

Thử nghiệm này tiếp tục hướng nghiên cứu thay thế tín hiệu hiện diện đơn giản từ
cảm biến hồng ngoại/RS485 bằng tín hiệu hành vi giàu ngữ cảnh hơn. Nếu cảm biến
hồng ngoại chỉ trả lời câu hỏi “có người trước kiosk hay không”, Holistic được
dùng để nghiên cứu câu hỏi khó hơn: người đó có đang hướng sự chú ý vào kiosk và
có khả năng cần hỗ trợ hay không.

- Mã thử nghiệm: `holistic_usage_research.py`
- Thư mục kết quả: `outputs/holistic_usage_tests/20260526_161238`
- Camera: `0`
- Thời lượng mục tiêu: `60.0` giây
- Thời lượng thực tế theo log: `48.196` giây, dừng bằng `q_or_escape`
- Số frame xử lý: `442`
- FPS xử lý trung bình: `9.17`
- Latency trung bình: `90.13 ms/frame`
- RAM trung bình: `639.83 MB`
- CPU trung bình: `91.58%`

Thử nghiệm này dùng **MediaPipe Holistic legacy**, không dùng MediaPipe Tasks:

- API chính: `mediapipe.python.solutions.holistic.Holistic`
- Cần phiên bản MediaPipe còn hỗ trợ Holistic legacy, hiện pin
  `mediapipe==0.10.14` trong `requirements-device.txt`
- Dữ liệu lấy từ cùng một pipeline: pose landmarks, face landmarks, eye/iris
  landmarks
- Voicebot chưa được tích hợp thật; state `NEED_SUPPORT` chỉ là kết luận logic
  nghiên cứu

Logic hiện tại là **rule-based**, không train model:

- `TOO_FAR`: có người nhưng kích thước vai/mặt còn nhỏ, chưa đủ gần.
- `POTENTIAL_USER`: người ở active zone, có mặt/mắt, gaze tương đối centered,
  và chưa di chuyển nhanh.
- `NEED_SUPPORT`: `POTENTIAL_USER` giữ liên tục đủ `usage_hold_sec`.
- `PERSON_PRESENT_NOT_ATTENDING`: có người trong active zone nhưng chưa đủ điều
  kiện attention candidate.

Trong kiến trúc hiện tại, chatbot thoại vẫn là module xử lý keyword, TTS và log
hội thoại. Do đó, kết quả `NEED_SUPPORT` trong thử nghiệm này nên được hiểu là
tín hiệu kích hoạt có điều kiện cho chatbot, không phải bản thân chatbot. Vision
cần đóng vai trò lọc ngữ cảnh trước khi chatbot bắt đầu chào, nghe và xử lý yêu
cầu.

## File Kết Quả

Thư mục kết quả có đủ dữ liệu để đánh giá:

- `raw.mp4`: video gốc.
- `annotated.mp4`: video có overlay debug.
- `config.json`: cấu hình lúc chạy.
- `metrics.csv`: số liệu tổng hợp.
- `frame_metrics.csv`: trạng thái theo từng giây.
- `events.csv`: event chuyển trạng thái.
- `summary.md`: summary tự sinh từ script.

Lưu ý về video: file `raw.mp4` và `annotated.mp4` có `442` frame và được ghi ở
`30 FPS`, nên khi mở xem video chỉ dài khoảng `14.733` giây. Trong khi đó log
runtime ghi thời lượng thực tế là `48.196` giây. Vì vậy khi đánh giá thời điểm
state, nên ưu tiên `events.csv` và `frame_metrics.csv`, không nên dựa vào thời
gian phát video.

## Kết Quả Định Lượng

Các mốc quan trọng từ `metrics.csv` và `events.csv`:

- `START -> TOO_FAR` tại `0.874s`.
- `TOO_FAR -> POTENTIAL_USER` tại `8.506s`.
- `attention_candidate_started` tại `8.506s`.
- `POTENTIAL_USER -> NEED_SUPPORT` tại `11.398s`.
- `need_support_detected` tại `11.398s`, sau khi attention giữ đủ `3.0s`.
- `manual_stop` tại `47.787s`.

Số frame theo state:

- `TOO_FAR`: `64` frame.
- `POTENTIAL_USER`: `84` frame.
- `NEED_SUPPORT`: `212` frame.
- `PERSON_PRESENT_NOT_ATTENDING`: `82` frame.

Nhận xét:

- Holistic nhận đúng đoạn đầu là `TOO_FAR`, chưa kích hoạt ngay khi người còn
  xa.
- Khi người tiến gần và đủ điều kiện mắt/gaze, hệ thống chuyển sang
  `POTENTIAL_USER`.
- Sau khoảng 3 giây giữ attention candidate, hệ thống chuyển sang `NEED_SUPPORT`.
  Đây là hành vi đúng với mục tiêu phát hiện người thật sự cần hỗ trợ.
- Sau khi đã vào `NEED_SUPPORT`, state vẫn có lúc rơi về
  `PERSON_PRESENT_NOT_ATTENDING`, sau đó quay lại `POTENTIAL_USER` và
  `NEED_SUPPORT`. Điều này cho thấy rule gaze/eye hiện tại còn nhạy và cần
  smoothing.

## So Sánh Nhanh Với Thử Nghiệm 01

Thử nghiệm 01 dùng MediaPipe Tasks `PoseLandmarker + FaceLandmarker`:

- FPS: `9.94`
- Latency trung bình: `84.14 ms/frame`
- RAM trung bình: `219.66 MB`
- Trigger mock voicebot tại `10.82s`

Thử nghiệm 02 dùng MediaPipe Holistic legacy:

- FPS: `9.17`
- Latency trung bình: `90.13 ms/frame`
- RAM trung bình: `639.83 MB`
- Vào `NEED_SUPPORT` tại `11.398s`

Kết luận so sánh:

- Holistic cho state nghiên cứu rõ hơn vì cùng lúc có pose, face, eye/iris trong
  một pipeline.
- Holistic nặng hơn đáng kể về RAM và CPU so với hướng MediaPipe Tasks hiện tại.
- Thời điểm phát hiện nhu cầu hỗ trợ gần tương đương Tasks, nhưng Holistic không
  cho lợi thế rõ rệt về tốc độ.
- Holistic hữu ích để nghiên cứu logic mắt/gaze, nhưng chưa nên thay runtime
  chính nếu thiết bị thật bị giới hạn tài nguyên.

## Đánh Giá Rule Holistic Hiện Tại

Điểm tốt:

- Có state rõ hơn so với boolean `attention`.
- Có thể phân biệt `POTENTIAL_USER`, `NEED_SUPPORT`, và
  `PERSON_PRESENT_NOT_ATTENDING`.
- Có log `movement_speed_ratio_per_sec`, `gaze_centered`, `avg_gaze_dx`, giúp
  phân tích rule sau mỗi video.

Điểm cần cải thiện:

1. Gaze rule đang nhạy. Từ `23s` trở đi, state chuyển qua lại giữa
   `NEED_SUPPORT`, `PERSON_PRESENT_NOT_ATTENDING`, và `POTENTIAL_USER`.
2. Chưa có session state. Khi đã vào `NEED_SUPPORT`, nếu mất attention rất ngắn
   thì không nên hạ trạng thái ngay.
3. Cần deactivation hold. Ví dụ chỉ rời `NEED_SUPPORT` khi mất attention liên
   tục 1-2 giây.
4. Movement filter hiện chưa được kích hoạt trong run này vì tốc độ luôn dưới
   threshold `0.45 frame-width/sec`. Cần thêm video người đi ngang nhanh để kiểm
   tra rule `PASSING_BY`.
5. Video writer đang dùng `capture_fps=30`, làm video phát nhanh hơn thời gian
   thực khi tốc độ xử lý chỉ khoảng 9 FPS. Nên ghi video theo FPS thực tế hoặc
   ghi timestamp overlay rõ hơn.

## Issues Của Thử Nghiệm 02

### Issue 01: Chi Phí Tính Toán Cao So Với Lợi Ích Quan Sát Được

Holistic dùng RAM trung bình `639.83 MB`, cao hơn đáng kể so với thử nghiệm
MediaPipe Tasks (`219.66 MB`). FPS trung bình cũng thấp hơn nhẹ (`9.17` so với
`9.94`). Trong bối cảnh kiosk chạy trên thiết bị cố định, chi phí tài nguyên là
yếu tố quan trọng vì hệ thống còn phải chạy UI, chatbot, TTS/STT và các tác vụ
backend khác.

Ảnh hưởng: Holistic có thể phù hợp để nghiên cứu, nhưng chưa phải lựa chọn tối
ưu để triển khai runtime chính nếu thiết bị bị giới hạn tài nguyên.

### Issue 02: Gaze Rule Chưa Ổn Định

State chuyển qua lại giữa `NEED_SUPPORT`, `PERSON_PRESENT_NOT_ATTENDING` và
`POTENTIAL_USER` sau mốc `23s`. Điều này cho thấy rule dựa trên eye/iris/gaze
đang nhạy với dao động landmark hoặc thay đổi nhỏ của khuôn mặt.

Ảnh hưởng: nếu dùng trực tiếp để điều khiển chatbot, hệ thống có thể thay đổi
trạng thái hội thoại quá nhanh so với cảm nhận tự nhiên của người dùng.

### Issue 03: Chưa Có Session-Level State

Sau khi đã xác định `NEED_SUPPORT`, hệ thống vẫn hạ state ngay khi mất điều kiện
attention candidate. Với chatbot thực tế, một phiên đã mở nên có độ trễ đóng
phiên, vì người dùng có thể quay mặt ngắn, nhìn giấy tờ, hoặc thao tác màn hình
mà không nhìn thẳng camera.

Ảnh hưởng: chatbot có thể bị ngắt hoặc thay đổi trạng thái khi người dùng vẫn
đang trong phiên tương tác hợp lệ.

### Issue 04: Video Output Không Đồng Bộ Với Thời Gian Thực

Log ghi thời lượng thực tế `48.196s`, nhưng video `442` frame được ghi ở
`30 FPS`, nên khi phát lại chỉ dài khoảng `14.733s`. Đây là vấn đề phương pháp
luận vì người xem video có thể hiểu sai thời điểm state transition nếu không đối
chiếu với log.

Ảnh hưởng: khó review thủ công và khó đối chiếu trực quan giữa video với
`events.csv`.

### Issue 05: Chưa Đủ Dữ Liệu Để Kết Luận Về Người Đi Ngang

Movement filter không được kích hoạt trong run này vì tốc độ luôn dưới threshold
`0.45 frame-width/sec`. Do đó, chưa thể kết luận rule `PASSING_BY` hoạt động tốt
trong các tình huống âm tính quan trọng.

Ảnh hưởng: Holistic chưa chứng minh được khả năng giảm false-positive đối với
người đi ngang, vốn là lý do chính để chuyển từ cảm biến hồng ngoại sang
computer vision.

## Kết Luận

Thử nghiệm 02 xác nhận MediaPipe Holistic có thể dùng để nghiên cứu logic
nhận diện người cần hỗ trợ, đặc biệt là phần mắt/iris/gaze. State
`NEED_SUPPORT` xuất hiện tại `11.398s`, hợp lý với cấu hình giữ attention `3.0s`.

Tuy nhiên Holistic tiêu tốn tài nguyên cao hơn nhiều so với MediaPipe Tasks và
chưa cho thấy lợi thế đủ rõ để thay runtime chính. Hướng phù hợp hiện tại là
giữ Holistic như công cụ nghiên cứu rule, còn runtime chính vẫn nên ưu tiên
MediaPipe Tasks nhẹ hơn.
