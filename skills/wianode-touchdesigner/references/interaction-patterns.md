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

## Exact quantity controls

When the user asks for an exact particle or instance count, do not drive a Particle SOP's `birth` parameter and assume it represents the current population. Birth rate combines with lifetime, frame rate, and internal limits, so most of the sensor range may saturate at the same count.

Prefer an explicit count stage such as a Script POP that creates `round(clamp(value, 0, 1) * max_count)` points, followed by a Copy POP. Keep positions deterministic if only the count should change. Test both endpoints and at least two interior values, then inspect low/high output images. The validated P1 balance-scale project used `0 → 0`, `0.1 → 30`, `0.9 → 270`, and `1 → 300`.

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

## Continuous actuator mappings

Build a preview-only chain first and leave its CHOP Execute DAT inactive. Confirm the physical port, SKU, configured mode, mechanical range, dead zone/rate limit, and stop method. After approval, send one exact bounded command and verify broker acceptance separately from physical movement. Arm continuous output only after the user confirms the physical response and explicitly authorizes the continuous mapping.

For an external bridge, use two interlocks: a bridge-level hardware-output flag and a TouchDesigner-level active/confirmed flag. Disable direct sensor-follow in the bridge so TouchDesigner remains the single owner of the mapping. If the request loses its response after a possible publish, do not retry blindly; inspect the bridge and ask whether the actuator moved.

A field-tested example mapped particle count `0..300` to P5 `SER0053` (`servo300`) over a user-confirmed `30..270°` mechanical range, with a `3°` dead zone and `0.12 s` minimum publish interval. Reconfirm these values for every different mechanism.

## Natural-language examples

- “让 P1 按钮切换两张图” → observe the P1 key, create/reuse a threshold or logic stage, drive the existing Switch TOP index, then capture the output TOP.
- “用光照控制圆的大小，暗处小、亮处大” → observe the actual light key, establish a measured light range, normalize and clamp it, map to the circle size parameter, then verify both node errors and output.
- “把加速度计 X 轴映射成立方体旋转并平滑一点” → confirm SEN0224, observe the x key, add a dead-zone/filter, map the chosen g range to degrees, then inspect the Render TOP.
- “让 P5 舵机转到 200°” → confirm SER0053 and `servo300`, preview `{"p5":"200"}`, obtain confirmation, publish once, and mark physical motion `待用户确认` unless observed by the user.
- “做一个旋钮控制粒子数量、粒子数量再像秤一样控制舵机的项目” → map the observed rotary key to an exact point count, smooth the count, preview the servo range while output is locked, send one confirmed midpoint test, then arm continuous output only after physical confirmation.

## Verification

After mapping sensor input, report the latest observed value and mapped output value when available. After a visual edit, use `get_top_image` on the final TOP. After a hardware publish, report only that the broker accepted the publish unless the user confirms the physical result.
