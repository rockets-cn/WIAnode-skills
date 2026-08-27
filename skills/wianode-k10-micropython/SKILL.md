---
name: wianode-k10-micropython
description: Create, upload, and troubleshoot UNIHIKER K10 MicroPython projects that exchange sensor and actuator data with DFRobot WIAnode over MQTT. Use when a user wants K10 buttons, sensors, screen, RGB, or buzzer to interact with WIAnode from MicroPython, or wants WIAnode sensor data displayed or processed on K10. Do not use for PlatformIO/Arduino projects, TouchDesigner, or WIAnode config.txt editing.
---

# WIAnode × UNIHIKER K10 with MicroPython

Turn the user's interaction description into a self-contained UNIHIKER K10 MicroPython project. K10 is an MQTT client; WIAnode is the broker. Keep both devices on the same reachable Wi-Fi network.

## Route the task

- Read [references/micropython-project.md](references/micropython-project.md) when creating, uploading, monitoring, or troubleshooting a MicroPython project, including firmware, upload ports, and the `main.py` auto-run rule.
- Read [references/mqtt-contract.md](references/mqtt-contract.md) before implementing WIAnode connection, packet parsing, or publishing.
- Read [references/interaction-patterns.md](references/interaction-patterns.md) when mapping K10 inputs/outputs to WIAnode data or actuators.
- Use `$wianode-config` first when WIAnode Wi-Fi, port modes, or attached SKUs are not configured. This skill must not edit the device's `config.txt`.
- Follow the installed `$unihiker-k10-micropython` skill for K10 MicroPython API lookup, firmware flashing, file upload, REPL verification, and port detection. This skill supplies the WIAnode-specific project shape and MQTT behavior.

## Prerequisites (firmware exclusivity)

K10 cannot run Arduino and MicroPython firmware at the same time. Confirm the board is actually running the MicroPython firmware before uploading:

- If the board runs Arduino firmware, `mpremote` fails with "could not enter raw repl". Flash the MicroPython firmware first (hold `BOOT`, press `RST`, release `BOOT`, flash, wait 30–60 s, press `RST`).
- Only `main.py` runs automatically on boot. Name the entry file `main.py`; other files must be imported via REPL.
- In V0.9.2 firmware, AI features and Wi-Fi cannot run at the same time (memory overflow). WIAnode projects need Wi-Fi, so do not combine them with `ai.*` camera features.
- Speech synthesis (`asr.add_tts_data()` / `asr.start_tts()`) exists only in the Chinese MicroPython firmware; do not present TTS as available on international firmware.

## Required context

Resolve only inputs needed by the requested interaction:

- Wi-Fi SSID and password for the network shared by K10 and WIAnode;
- WIAnode IP shown after pressing `WKUP`;
- confirmed WIAnode port, module, SKU, and configured mode;
- which K10 input or output is involved;
- source and destination ranges, smoothing, threshold, rate limit, and fail-safe behavior.

Keep Wi-Fi credentials in the template's `secrets.py`, which the template excludes from Git. Never repeat them in summaries, REPL output, screenshots, or generated reports.

## Workflow

1. Copy `assets/template/wianode-k10-micropython/` into a new project directory. Do not create PlatformIO, Arduino, or TouchDesigner files.
2. Copy `secrets.example.py` to `secrets.py` and fill only the supplied Wi-Fi and WIAnode values. Do not commit the populated file. The template halts with an on-screen warning if it is uploaded with placeholder values.
3. Confirm the K10 runs MicroPython firmware (see prerequisites); if not, guide the user through flashing with the installed `$unihiker-k10-micropython` skill.
4. Build a sensor-only tracer bullet first: connect Wi-Fi, connect MQTT with the template's field-tested design (`umqtt.simple` with two connections: `k10i-*` subscribes to `topic_input`, `k10o-*` publishes and never subscribes), parse strict JSON with the firmware's `json` module (not `ujson`, which MicroPython ≥1.21 renamed), print credential-free diagnostics, and update the K10 screen with partial redraws only.
5. Add the requested mapping as the smallest visible change. Keep the main loop non-blocking, use bounded reconnect intervals, clamp mapped values, rate-limit physical outputs, and never redraw from the MQTT callback—set a flag and render from the loop.
6. Upload with `k10-micropython upload-mp main.py` or `mpremote cp main.py :main.py`, then reset the board so `main.py` auto-runs.
7. Verify through the REPL serial console: Wi-Fi connected, MQTT connected, `topic_input` subscription, and at least one real packet when available. Never claim a physical output occurred without user observation.

## Hardware-output confirmation gate

The template sets `ENABLE_ACTUATOR_OUTPUT` to `False`. Leave it disabled for sensor display, logging, dashboards, and other read-only interactions.

Before generating or uploading firmware that can publish to `topic_output`, show:

- WIAnode IP and exact JSON payload or bounded payload rule;
- physical port, module, SKU, and configured mode;
- allowed range, clamp, publish rate, and stop/fail-safe behavior;
- the K10 event that will trigger the command.

Ask `确认生成并上传上述 WIAnode 控制逻辑吗？` Only after affirmative confirmation may the project set `ENABLE_ACTUATOR_OUTPUT` to `True` and call the publish helper. Do not use retained actuator messages. A request to display sensor data or create a project does not authorize physical output.

## Completion evidence

Report separately:

- project path, firmware mode, and upload method used;
- Wi-Fi and MQTT connection state without credentials;
- observed `topic_input` keys and latest safe values;
- screen refresh approach (partial redraws) and, for reported latency, the packet receive and UI update behavior as separate observations;
- actuator logic enabled or disabled;
- commands actually published and physical results still `待用户确认`.

Do not claim completion from a successful upload alone. REPL/serial verification is a distinct evidence stage.

## Shared experience from the field-tested PlatformIO variant

The following behaviors were validated with a real K10 (`unihiker_k10`, LVGL 8.3.10) driving a WIAnode with a P1 DFR0054 knob mapped to a P5 SER0053 300° servo. The MicroPython template reimplements the same design; the principles transfer, but the MicroPython firmware API details must be checked against the official docs and the installed `$unihiker-k10-micropython` skill.

- Re-run port detection immediately before each upload instead of trusting a saved COM number; a replugged K10 can re-enumerate.
- For continuous control, compute the mapped target from the current sensor value every loop and publish only when it moved beyond the dead zone; do not gate the actuator on the UI dirty flag, which the renderer may consume first.
- Map unknown analog ranges onto the confirmed mechanical range using the observed dynamic range instead of guessing a full scale. Apply a dead zone of at least 1° on the mapped output, clamp to the confirmed range, and publish only on real movement.
- Discover I2C module keys from the real packet by case-insensitive fragment match (e.g. `lux`) instead of hard-coding an unverified key. See [references/mqtt-contract.md](references/mqtt-contract.md).
- A publish log is not physical confirmation. Ask the user to verify the actuator moved.

## Field-tested MicroPython specifics (K10 v0.9.2 firmware, 2026-08)

Validated on a real K10 against a real WIAnode; these override the generic guidance above where they conflict:

- **Do not use `k10_base.MqttClient`.** It reconnects in a tight loop and breaks QoS 1 PUBACK handling (`AssertionError` in `umqtt.robust.publish`); WIAnode outputs driven through it behave erratically. Use the firmware's `umqtt.simple.MQTTClient` directly with QoS 0 compact payloads (`{"p5":"270"}`), exactly like the PlatformIO version. `mqtt.client.publish(..., qos=0)` on the wrapper is a workaround but the wrapper's reconnect loop remains.
- **WIAnode applies `topic_output` only from connections that are not subscribed to `topic_input`** (and not from client IDs with a persisted session that subscribed). A single subscribed connection's commands are ignored, so the dashboard uses two connections: `k10i-*` subscribes/receives, `k10o-*` publishes and never subscribes.
- **Power-cycle the WIAnode when outputs stop being applied.** It keeps per-client session state; after heavy reconnects (e.g. the wrapper era) a reboot clears it and commands work again. A PC client with a fresh client ID is unaffected, which is a useful isolation test.
- **The knob value is quantized to 0.01 (~2.4° on a 240° span).** Snap the value to 0.01 and use a dead zone above one quantum (3° in the reference project); a 1° dead zone oscillates the servo between adjacent angles on ADC noise.
- **Receive rate**: the WIAnode broker publishes at ~50 Hz; the K10's `umqtt.simple` `check_msg()` drained from the main loop achieves ~10–20 Hz (screen SPI work throttles it). Coalesce to the latest value and keep chart redraws throttled (the reference project redraws the trend chart at most every 500 ms).

## Reference implementation

`assets/template/wianode-k10-micropython/` is the reference implementation: a read-only WIAnode sensor dashboard in MicroPython with partial screen redraws, MQTT reconnect with re-subscribe, credential-free diagnostics, and a confirmation-gated publish helper. Copy it as a starting point; keep `secrets.py` out of Git (the template `.gitignore` already excludes it).

`projects/wianode-k10-micropython-dashboard/` in this repository is a full MicroPython port of the field-tested LVGL dashboard: P1 knob → P5 servo (30–270°, 1° dead zone), P2 sound, SEN0228 lux with a scrolling trend chart, and a system status card. Its `ENABLE_ACTUATOR_OUTPUT` was enabled only after the confirmation gate was applied, matching the PlatformIO original's confirmed mapping.
