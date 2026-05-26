# Device Runtime Setup

Thu muc nay chay rieng test nhan dien nguoi dang su dung kiosk tren thiet bi that.

Mac dinh moi thu duoc neo theo chinh thu muc `experiments/device_runtime`, nen co the copy sang may khac ma khong phu thuoc duong dan `D:\work\...`.

## Cau truc sau khi setup

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

## Cai dat tren may moi

Chay tu root project:

```powershell
python experiments\device_runtime\setup_device_runtime.py
```

Script se:

- Tao venv rieng tai `experiments/device_runtime/.venv`.
- Cai cac thu vien can thiet: MediaPipe, OpenCV, NumPy, psutil.
- Tai 2 model MediaPipe vao `experiments/device_runtime/models`.

Neu muon cai vao Python/venv dang kich hoat:

```powershell
python experiments\device_runtime\setup_device_runtime.py --skip-venv
```

Neu da co model va chi muon cai thu vien:

```powershell
python experiments\device_runtime\setup_device_runtime.py --skip-models
```

## Chay test

Neu dung venv rieng do script tao:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py
```

Neu camera khong phai index `0`:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py --camera 1
```

Ket qua se ghi vao:

```text
experiments/device_runtime/outputs/device_usage_tests/<timestamp>/
```

## Ghi chu model

Mac dinh runtime can:

- `models/pose_landmarker_lite.task`
- `models/face_landmarker.task`

Neu model nam o thu muc khac:

```powershell
experiments\device_runtime\.venv\Scripts\python.exe experiments\device_runtime\person_usage_device_test.py --model-dir D:\path\to\models
```
