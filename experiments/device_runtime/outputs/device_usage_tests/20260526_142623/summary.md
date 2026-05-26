# Device Usage Test Summary

This run is a webcam-only device feasibility test. Voicebot integration is mocked by events only.

## Config

- Camera: `0`
- Duration target: `60.0` seconds
- Usage hold: `3.0` seconds

## Metrics

- FPS: `9.94`
- Avg latency ms/frame: `84.14`
- Median latency ms/frame: `83.2`
- Avg CPU usage: `62.14%`
- Max CPU usage: `133.0%`
- Avg RAM: `219.66 MB`
- Max RAM: `220.23 MB`
- Active-zone frames: `298`
- Attention frames: `160`
- Active zone first sec: `5.371`
- Attention first sec: `7.429`
- Voicebot mock open sec: `10.82`
- Voicebot mock opened: `True`

## Events

- 5.371s: `active_zone_entered` - ACTIVE
- 7.429s: `attention_started` - zone_attention_rule
- 7.619s: `attention_lost` - countdown_reset_at_0.00s
- 7.804s: `attention_started` - zone_attention_rule
- 10.82s: `greeting_triggered` - attention_sustained_3.0s
- 10.82s: `voicebot_mock_opened` - mock_only_no_voicebot_integration
- 18.668s: `attention_lost` - countdown_reset_at_0.00s
- 18.766s: `attention_started` - zone_attention_rule
- 19.344s: `attention_lost` - countdown_reset_at_0.00s
- 22.166s: `active_zone_exited` - TOO_FAR
- 25.844s: `active_zone_entered` - ACTIVE
- 26.979s: `active_zone_exited` - TOO_FAR
- 29.547s: `active_zone_entered` - ACTIVE
- 32.921s: `attention_started` - zone_attention_rule
- 35.15s: `attention_lost` - countdown_reset_at_0.00s
- 35.435s: `active_zone_exited` - TOO_FAR
- 39.829s: `active_zone_entered` - ACTIVE
- 39.923s: `attention_started` - zone_attention_rule
- 40.61s: `attention_lost` - countdown_reset_at_0.00s
- 41.004s: `active_zone_exited` - TOO_FAR
- 44.166s: `active_zone_entered` - ACTIVE
- 44.166s: `attention_started` - zone_attention_rule
- 44.26s: `attention_lost` - countdown_reset_at_0.00s
- 45.678s: `attention_started` - zone_attention_rule
- 47.334s: `attention_lost` - countdown_reset_at_0.00s
- 48.519s: `attention_started` - zone_attention_rule
- 48.717s: `manual_stop` - q_or_escape
