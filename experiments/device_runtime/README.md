# Thiết Lập Device Runtime

Thư mục này dùng để chạy riêng phần thử nghiệm nhận diện người đang sử dụng kiosk trên thiết bị thật.

Mặc định mọi đường dẫn được neo theo chính thư mục `experiments/device_runtime`, nên có thể copy sang máy khác mà không phụ thuộc đường dẫn `D:\work\...`.

## Cấu Trúc Sau Khi Setup

```text
experiments/device_runtime/
  person_usage_device_test.py
  setup_device_runtime.py
  requirements-device.txt
  models/
    pose_landmarker_lite.task
    face_landmarker.task
  outputs/
    device_usage_tests/
```

## Cài Đặt Trên Máy Mới

Chạy từ root project:

```powershell
python experiments\device_runtime\setup_device_runtime.py
```

Script sẽ:

- Tạo venv riêng tại `experiments/device_runtime/.venv`.
- Cài các thư viện cần thiết: MediaPipe, OpenCV, NumPy, psutil.
- Tải 2 model MediaPipe vào `experiments/device_runtime/models`.

Lưu ý: `requirements-device.txt` đang pin `mediapipe==0.10.14` vì script
`holistic_usage_research.py` dùng MediaPipe Holistic legacy
`mediapipe.python.solutions.holistic`. Không dùng `pip install -U mediapipe`
cho venv này, vì bản mới hơn có thể không còn module Holistic legacy.

Nếu muốn cài vào Python/venv đang kích hoạt:

```powershell
python experiments\device_runtime\setup_device_runtime.py --skip-venv
```

Nếu đã có model và chỉ muốn cài thư viện:

```powershell
python experiments\device_runtime\setup_device_runtime.py --skip-models
```

Nếu venv đã lỡ cài MediaPipe bản mới và chạy Holistic bị lỗi, cài lại dependency
đã pin:

```powershell
python -m pip install --force-reinstall -r experiments\device_runtime\requirements-device.txt
```

## Chạy Test Runtime Chính

Nếu dùng venv riêng do script tạo:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py
```

Nếu camera không phải index `0`:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py --camera 1
```

Kết quả sẽ ghi vào:

```text
experiments/device_runtime/outputs/device_usage_tests/<timestamp>/
```

Review kết quả thử nghiệm MediaPipe Tasks hiện tại được ghi tại:

```text
experiments/device_runtime/EXPERIMENT_01_REVIEW.md
```

## Chạy Holistic Research

Script này dùng `mp.solutions.holistic` để nghiên cứu thêm logic pose + face + iris trong một pipeline riêng. Script này không thay thế runtime chính.

Yêu cầu phiên bản: `mediapipe==0.10.14` để còn module Holistic legacy.

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\holistic_usage_research.py --duration 10
```

Kết quả sẽ ghi vào:

```text
experiments/device_runtime/outputs/holistic_usage_tests/<timestamp>/
```

Review kết quả thử nghiệm Holistic hiện tại được ghi tại:

```text
experiments/device_runtime/EXPERIMENT_02_HOLISTIC_REVIEW.md
```

## Bối Cảnh Nghiên Cứu Và Issues Chung

Tài liệu tổng hợp bối cảnh chuyển từ cảm biến hồng ngoại/RS485 sang computer
vision, đồng thời mô tả mối liên hệ với chatbot hiện tại:

```text
experiments/device_runtime/RESEARCH_CONTEXT_AND_ISSUES.md
```

## Kiến Trúc Voicebot Phân Tán

Tài liệu mô tả hướng triển khai hai máy: kiosk i5 chạy camera/vision/ghi âm/TTS
Windows, máy Ryzen 9HX + RTX 5060 chạy faster-whisper và RAG qua Ethernet:

```text
experiments/device_runtime/DISTRIBUTED_VOICEBOT_PIPELINE.md
```

## Ghi Chú Model

Mặc định runtime chính cần:

- `models/pose_landmarker_lite.task`
- `models/face_landmarker.task`

Nếu model nằm ở thư mục khác:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py --model-dir D:\path\to\models
```
