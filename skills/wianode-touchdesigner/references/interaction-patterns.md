# WIAnode interaction patterns

Read this reference when translating a natural-language interaction into TouchDesigner nodes or when preparing a WIAnode actuator command. Sensor/SKU facts are based on the [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), checked 2026-08-25.

## Build a mapping explicitly

For each requested interaction, resolve this chain before editing:

```text
physical module + confirmed SKU/port
→ observed MQTT key
→ normalization/clamp
→ optional filter or threshold
→ TouchDesigner target parameter
→ visible verification
```

Use an existing Select/Math/Filter CHOP chain when it already expresses the mapping. For a new continuous mapping, prefer visible CHOP operators over a hidden per-frame Python callback. Use a parameter expression only when the mapping is simple and the dependency remains obvious.

Always state the source and destination ranges. Clamp before applying values that can destabilize a visual, audio level, or physical actuator. When the user says “更灵敏”“平滑一点”“反过来”, modify the normalization/filter stage rather than rebuilding the bridge.

## Common inputs

| Module / confirmed SKU | Typical observed data | Useful mapping |
| --- | --- | --- |
| Button DFR0029 on P1–P4 | `pN_input_val`, usually 0/1 | switch, trigger, gate |
| DHT11 DFR0067 | temperature and humidity keys | color, level, rate |
| Sound DFR0034 | `pN_input_val` | scale to 0–1, smooth before visual/audio use |
| Light DFR0026 or I2C SEN0228 | input value or `Lux` | normalize measured environment range to brightness |
| Ultrasonic SEN0304 | `Distance` | clamp a chosen near/far range, optionally invert |
| Accelerometer SEN0224 | x/y/z | dead-zone and smooth before rotation/position mapping |
| Gesture SEN0561 | `Gesture`, documented values 1–4 | map discrete values to Switch/Select behavior |

Use the live packet's exact key names. The table is guidance for interpretation, not permission to guess a key.

## Common outputs

| Module / confirmed SKU | Port/mode | Payload example | Safety rule |
| --- | --- | --- | --- |
| 180° servo SER0006 | P5/P6, `servo180` | `{"p5":"90"}` | clamp 0–180 |
| 300° servo SER0053 | P5/P6, `servo300` | `{"p5":"200"}` | clamp 0–300 |
| 360° servo SER0043 | P5/P6, `servo360` | device-mode-specific value | inspect current project/device behavior; do not assume angle semantics |
| WS2812 strip FIT0656 | configured P port, `ws2812` | `{"p1":"66 42 59 64 48 63 63 54 67"}` | require exactly 3 RGB integers per intended pixel, each 0–255 |

Actuator payload values are strings in DFRobot's documented examples. Use strict JSON and the hardware-output confirmation gate. Do not infer a servo's safe mechanical travel from only its electrical range.

## Natural-language examples

- “让 P1 按钮切换两张图” → observe the P1 key, create/reuse a threshold or logic stage, drive the existing Switch TOP index, then capture the output TOP.
- “用光照控制圆的大小，暗处小、亮处大” → observe the actual light key, establish a measured light range, normalize and clamp it, map to the circle size parameter, then verify both node errors and output.
- “把加速度计 X 轴映射成立方体旋转并平滑一点” → confirm SEN0224, observe the x key, add a dead-zone/filter, map the chosen g range to degrees, then inspect the Render TOP.
- “让 P5 舵机转到 200°” → confirm SER0053 and `servo300`, preview `{"p5":"200"}`, obtain confirmation, publish once, and mark physical motion `待用户确认` unless observed by the user.

## Verification

After mapping sensor input, report the latest observed value and mapped output value when available. After a visual edit, use `get_top_image` on the final TOP. After a hardware publish, report only that the broker accepted the publish unless the user confirms the physical result.
