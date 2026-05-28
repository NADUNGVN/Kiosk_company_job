# WebSocket Backend API

This folder is a backend package. The primary service entrypoint is:

```powershell
.\.venv\Scripts\python.exe .\backend_server.py --config .\backend_config.json
```

## HTTP Endpoints

- `GET /health`: readiness, scheduler state, active sessions, startup errors.
- `GET /api/config`: current public runtime settings.
- `PATCH /api/config`: update runtime-safe settings.
- `GET /api/metrics`: session and scheduler metrics.
- `GET /`: bundled browser client for manual testing.

## WebSocket Endpoint

```text
ws://127.0.0.1:8010/ws/transcribe
```

On connect, the server sends session bootstrap events. The exact order can
include `status` first, followed by:

- `hello`: assigned `sessionId`, settings, limits, supported engines.
- `ready`: sent when ASR workers are ready.

## Text Commands

Send JSON text messages:

```json
{"type":"start"}
```

```json
{"type":"stop"}
```

```json
{"type":"clear"}
```

```json
{"type":"ping"}
```

```json
{"type":"metrics"}
```

## Audio Messages

Send binary messages using this layout:

```text
uint32 little-endian metadata_json_byte_length
metadata JSON bytes
pcm_s16le audio bytes
```

Required metadata:

```json
{
  "sampleRate": 16000,
  "channels": 1,
  "format": "pcm_s16le",
  "frames": 512
}
```

Notes:

- `sampleRate` can be different from 16000; the backend resamples to 16 kHz.
- `channels` can be 1 to 8; multi-channel input is downmixed to mono.
- `frames` is optional, but if present it must match payload length.
- `format` currently must be `pcm_s16le`.

## Server Events

Important response events:

- `realtime`: interim transcript update.
- `final`: finalized transcript segment.
- `timeline`: recording/transcription lifecycle events.
- `status`: session state update.
- `warning`: recoverable issue, such as dropped realtime work.
- `error`: command, audio packet, admission, or inference error.
- `pong`: response to `ping`.
- `metrics`: response to `metrics`.
