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

Nếu muốn cài vào Python/venv đang kích hoạt:

```powershell
python experiments\device_runtime\setup_device_runtime.py --skip-venv
```

Nếu đã có model và chỉ muốn cài thư viện:

```powershell
python experiments\device_runtime\setup_device_runtime.py --skip-models
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

## Chạy Holistic Research

Script này dùng `mp.solutions.holistic` để nghiên cứu thêm logic pose + face + iris trong một pipeline riêng. Script này không thay thế runtime chính.

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\holistic_usage_research.py --duration 10
```

Kết quả sẽ ghi vào:

```text
experiments/device_runtime/outputs/holistic_usage_tests/<timestamp>/
```

## Ghi Chú Model

Mặc định runtime chính cần:

- `models/pose_landmarker_lite.task`
- `models/face_landmarker.task`

Nếu model nằm ở thư mục khác:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py --model-dir D:\path\to\models
```
