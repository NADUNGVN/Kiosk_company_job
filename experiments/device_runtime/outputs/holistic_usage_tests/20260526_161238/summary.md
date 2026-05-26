# Holistic Usage Research Summary

This run studies MediaPipe Holistic for kiosk person usage detection.

## Config

- Camera: `0`
- Duration target: `60.0` seconds
- Usage hold: `3.0` seconds
- Passing speed threshold: `0.45` frame-width/sec

## Metrics

- FPS: `9.17`
- Avg latency ms/frame: `90.13`
- Median latency ms/frame: `91.01`
- Avg CPU usage: `91.58%`
- Max CPU usage: `198.9%`
- Avg RAM: `639.83 MB`
- Max RAM: `641.23 MB`
- Attention first sec: `8.506`
- Support first sec: `11.398`

## State Counts

- `NEED_SUPPORT`: `212` frames
- `PERSON_PRESENT_NOT_ATTENDING`: `82` frames
- `POTENTIAL_USER`: `84` frames
- `TOO_FAR`: `64` frames

## Events

- 0.874s: `state_changed` - START -> TOO_FAR
- 8.506s: `state_changed` - TOO_FAR -> POTENTIAL_USER
- 8.506s: `attention_candidate_started` - holistic_rule
- 11.398s: `state_changed` - POTENTIAL_USER -> NEED_SUPPORT
- 11.398s: `need_support_detected` - attention_sustained_3.0s
- 23.043s: `state_changed` - NEED_SUPPORT -> PERSON_PRESENT_NOT_ATTENDING
- 23.129s: `state_changed` - PERSON_PRESENT_NOT_ATTENDING -> POTENTIAL_USER
- 26.094s: `state_changed` - POTENTIAL_USER -> NEED_SUPPORT
- 28.984s: `state_changed` - NEED_SUPPORT -> PERSON_PRESENT_NOT_ATTENDING
- 29.835s: `state_changed` - PERSON_PRESENT_NOT_ATTENDING -> POTENTIAL_USER
- 30.403s: `state_changed` - POTENTIAL_USER -> PERSON_PRESENT_NOT_ATTENDING
- 38.456s: `state_changed` - PERSON_PRESENT_NOT_ATTENDING -> POTENTIAL_USER
- 41.348s: `state_changed` - POTENTIAL_USER -> NEED_SUPPORT
- 47.787s: `manual_stop` - q_or_escape
