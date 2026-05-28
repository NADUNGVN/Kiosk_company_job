# RealtimeSTT Zipformer VI Backend

Portable Vietnamese realtime STT backend for the tested pipeline.

This folder is intended to be copied into another project. It contains only the
runtime pieces needed for the current Sherpa-ONNX Zipformer Vietnamese backend:

- `RealtimeSTT/`: local patched RealtimeSTT runtime.
- `server_app/`: FastAPI/WebSocket implementation and static test UI.
- `models/`: bundled Zipformer Vietnamese model and sample wav.
- `backend_server.py`: backend service entrypoint.
- `backend_config.json`: backend config.
- `terminal_demo.py`: optional local microphone/sample smoke test.
- `requirements.txt`: backend dependencies.

## Install

```powershell
cd path\to\RealtimeSTT_Zipformer_VI_Server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Backend Service

```powershell
.\.venv\Scripts\python.exe .\backend_server.py
```

Open the bundled manual test UI:

```text
http://127.0.0.1:8010
```

The backend WebSocket endpoint is:

```text
ws://127.0.0.1:8010/ws/transcribe
```

See `WEBSOCKET_API.md` for the message protocol.

Override host or port:

```powershell
.\.venv\Scripts\python.exe .\backend_server.py --host 0.0.0.0 --port 8010
```

Print resolved config:

```powershell
.\.venv\Scripts\python.exe .\backend_server.py --print-config
```

## Smoke Test

```powershell
.\.venv\Scripts\python.exe .\terminal_demo.py --sample
```

## Optional Terminal Test

```powershell
.\.venv\Scripts\python.exe .\terminal_demo.py
```

Use a specific microphone:

```powershell
.\.venv\Scripts\python.exe .\terminal_demo.py --input-device-index 1
```

If you want to reuse an existing Python environment instead of `.venv`:

```powershell
C:\path\to\python.exe .\terminal_demo.py --sample
```

## Notes

- The bundled STT model runs on CPU through `sherpa-onnx`.
- The original upstream test folders, docs, examples, and alternate engines are
  not included.
- Do not copy only `server_app/`; it still imports the local `RealtimeSTT/`
  package and uses the model in `models/`.
