# K10 and WIAnode interaction patterns (MicroPython)

Read this reference when mapping K10 inputs/outputs to WIAnode data or actuators. Code uses the K10 MicroPython firmware APIs (`unihiker_k10`, `k10_base`) and the WIAnode MQTT contract in `mqtt-contract.md`.

## WIAnode sensors to K10

| Request | Mapping |
| --- | --- |
| Show a WIAnode sensor on K10 | observed MQTT key → `json` value → erased row region → partial redraw |
| Use a button as a K10 indicator | `pN_input_val` → threshold 0/1 → K10 RGB or screen state |
| Alarm on temperature/distance | observed key → validated numeric value → threshold/hysteresis → K10 buzzer/RGB |
| Visualize movement | accelerometer/distance key → clamp/normalize → small screen region or indicator |

Never redraw the whole K10 screen in the MQTT callback. Save the latest parsed values and set a dirty flag; update only the affected rows from the main loop.

For streams faster than 10 Hz, separate network ingestion from presentation: receive and validate every packet, overwrite pending values, and render only the latest dirty state.

## K10 inputs to WIAnode actuators

| K10 source | WIAnode target | Required controls |
| --- | --- | --- |
| Button A/B | discrete servo position or light state | edge detection, one publish per press, confirmed payload |
| K10 accelerometer | servo angle | dead zone, smoothing, clamp, publish interval, mechanical safe range |
| K10 light sensor | WS2812 brightness/color | normalize, RGB clamp 0–255, pixel-count validation, publish interval |
| Timer/state machine | actuator sequence | bounded steps, explicit stop condition, no retained messages |
| WIAnode P1 knob forwarded via K10 | P5/P6 servo angle | dynamic-range mapping, dead zone, clamp, publish on real movement, fail-safe on disconnect |

These mappings require `ENABLE_ACTUATOR_OUTPUT = True`, which may be set only after the confirmation preview in `SKILL.md`.

### Confirmed knob-to-servo recipe (P1 DFR0054 → P5 SER0053)

Preview and confirm P5, `SER0053`, `servo300`, the mechanical safe range (30–270°), the dead zone (≥1°), the publish rule ("every knob change, bounded by the 0.02 s WIAnode interval"), and payload `{"p5":"<angle>"}` before enabling output. Then:

```python
servo_min = 30
servo_max = 270
servo_deadzone_deg = 1
desired_servo_angle = None

def map_knob_to_servo_angle():
    span = knob_max - knob_min
    if span < 1e-6:
        return servo_min
    ratio = max(0.0, min(1.0, (knob_value - knob_min) / span))
    return servo_min + int(round(ratio * (servo_max - servo_min)))

def handle_knob_servo():
    global desired_servo_angle
    if not ENABLE_ACTUATOR_OUTPUT or knob_value is None:
        return
    # Do NOT gate on the UI dirty flag: the renderer may consume it first.
    target = map_knob_to_servo_angle()
    if desired_servo_angle is not None and abs(target - desired_servo_angle) < servo_deadzone_deg:
        return
    if publish_wianode_command({"p5": str(target)}):
        desired_servo_angle = target
```

Call `handle_knob_servo()` from the main loop without blocking. The observed dynamic range (`knob_min..knob_max`) adapts to the actual potentiometer travel instead of guessing a full scale; the dead zone absorbs one-pixel jitter in the raw ADC. A successful publish is not physical confirmation—ask the user to verify the servo moved.

### Confirmed K10 A → P5 SER0053 recipe

Use this shape only after P5, `SER0053`, `servo300`, the 0–300 protocol range, the mechanical safe range, and payload `{"p5":"200"}` have been previewed and confirmed. Set `ENABLE_ACTUATOR_OUTPUT` to `True`, add edge detection so holding the button does not publish repeatedly, and call the template helper:

```python
previous_button_a = False

def handle_servo_command():
    global previous_button_a
    pressed = bt_a.status() == 1
    if pressed and not previous_button_a:
        published = publish_wianode_command({"p5": "200"})
        print("P5 command published" if published else "P5 command not published")
    previous_button_a = pressed
```

Call `handle_servo_command()` from the main loop without adding a blocking delay. This recipe proves only that MQTT accepted the publish; the user must confirm physical motion.

## Example interpretations

- "在 K10 上显示 WIAnode 的温湿度" → subscribe, observe exact temperature/humidity keys, then preserve their row assignments; the base template displays up to three fields while discovering the packet.
- "WIAnode 按钮按下时让 K10 亮绿灯" → map the observed button key to K10 RGB; no `topic_output` publishing is needed.
- "按 K10 A 键让 P5 的 SER0053 转到 200°" → confirm P5, SER0053, and `servo300`; preview `{"p5":"200"}`; enable output only after confirmation; publish once on the button edge.
- "用 K10 倾斜控制 WIAnode 舵机" → require a confirmed servo type and mechanical range; filter and rate-limit K10 acceleration before mapping; provide an explicit stop/fail-safe rule.

## Completion checks

- Verify the actual incoming key rather than only the expected naming pattern.
- Report the input value, mapped value, clamp, and publish interval.
- Distinguish a successful MQTT publish from confirmed physical motion.
- Keep REPL messages concise and credential-free.
