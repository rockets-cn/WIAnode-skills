# K10 and WIAnode interaction patterns

Read this reference when mapping K10 inputs/outputs to WIAnode data or actuators.

## WIAnode sensors to K10

| Request | Mapping |
| --- | --- |
| Show a WIAnode sensor on K10 | observed MQTT key → JSON value → padded Canvas row or persistent LVGL widget → partial update |
| Use a button as a K10 indicator | `pN_input_val` → threshold 0/1 → K10 RGB or screen state |
| Alarm on temperature/distance | observed key → validated numeric value → threshold/hysteresis → K10 buzzer/RGB |
| Visualize movement | accelerometer/distance key → clamp/normalize → small screen region or indicator |

Do not redraw the entire K10 screen in the MQTT callback. Save the latest value, then update only the affected row or region from the main loop.

For streams faster than 10 Hz, separate network ingestion from presentation: receive and validate every packet, overwrite pending values, and render only the latest dirty state. Read `lvgl-high-rate-dashboard.md` before building a native LVGL dashboard or tuning apparent display latency.

## K10 inputs to WIAnode actuators

| K10 source | WIAnode target | Required controls |
| --- | --- | --- |
| Button A/B | discrete servo position or light state | edge detection, one publish per press, confirmed payload |
| K10 accelerometer | servo angle | dead zone, smoothing, clamp, publish interval, mechanical safe range |
| K10 light sensor | WS2812 brightness/color | normalize, RGB clamp 0–255, pixel-count validation, publish interval |
| Timer/state machine | actuator sequence | bounded steps, explicit stop condition, no retained messages |

These mappings require `ENABLE_ACTUATOR_OUTPUT = true`, which may be set only after the confirmation preview in `SKILL.md`.

### Confirmed K10 A → P5 SER0053 recipe

Use this shape only after P5, `SER0053`, `servo300`, the 0–300 protocol range, the mechanical safe range, and payload `{"p5":"200"}` have been previewed and confirmed. Set `ENABLE_ACTUATOR_OUTPUT` to `true`, add edge detection so holding the button does not publish repeatedly, and call the existing helper:

```cpp
bool previousButtonA = false;

void handleConfirmedServoCommand() {
  const bool buttonA = k10.buttonA->isPressed();
  if (buttonA && !previousButtonA) {
    JsonDocument command;
    command["p5"] = "200";
    const bool published = publishWianodeCommand(command);
    Serial.println(published ? "P5 command published"
                             : "P5 command not published");
  }
  previousButtonA = buttonA;
}
```

Call `handleConfirmedServoCommand()` from `loop()` without adding a blocking delay. This recipe proves only that MQTT accepted the publish; the user must confirm physical motion.

## Example interpretations

- “在 K10 上显示 WIAnode 的温湿度” → subscribe, observe exact temperature/humidity keys, then preserve their row assignments; the base template displays up to three fields while discovering the packet.
- “WIAnode 按钮按下时让 K10 亮绿灯” → map the observed button key to K10 RGB; no `topic_output` publishing is needed.
- “按 K10 A 键让 P5 的 SER0053 转到 200°” → confirm P5, SER0053, and `servo300`; preview `{"p5":"200"}`; enable output only after confirmation; publish once on the button edge.
- “用 K10 倾斜控制 WIAnode 舵机” → require a confirmed servo type and mechanical range; filter and rate-limit K10 acceleration before mapping; provide an explicit stop/fail-safe rule.

## Completion checks

- Verify the actual incoming key rather than only the expected naming pattern.
- Report the input value, mapped value, clamp, and publish interval.
- Distinguish a successful MQTT publish from confirmed physical motion.
- Keep serial messages concise and credential-free.
