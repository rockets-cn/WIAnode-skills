---
name: wianode-k10-platformio
description: Create, build, upload, and troubleshoot UNIHIKER K10 PlatformIO projects that exchange sensor and actuator data with DFRobot WIAnode over MQTT. Use when a user wants K10 buttons, sensors, screen, RGB, or buzzer to interact with WIAnode, or wants WIAnode sensor data displayed or processed on K10. Do not use for MicroPython, Arduino CLI projects, TouchDesigner, or WIAnode config.txt editing.
---

# WIAnode × UNIHIKER K10 with PlatformIO

Turn the user's interaction description into a self-contained UNIHIKER K10 PlatformIO project. K10 is an MQTT client; WIAnode is the broker. Keep both devices on the same reachable Wi-Fi network.

## Route the task

- Read [references/platformio-project.md](references/platformio-project.md) when creating, building, uploading, monitoring, or diagnosing a project.
- Read [references/mqtt-contract.md](references/mqtt-contract.md) before implementing WIAnode connection, packet parsing, or publishing.
- Read [references/interaction-patterns.md](references/interaction-patterns.md) when mapping K10 inputs/outputs to WIAnode data or actuators.
- Read [references/lvgl-high-rate-dashboard.md](references/lvgl-high-rate-dashboard.md) when the user wants a polished LVGL interface, the WIAnode interval is below 100 ms, or the screen appears delayed despite frequent packets.
- Use `$wianode-config` first when WIAnode Wi-Fi, port modes, or attached SKUs are not configured. This skill must not edit the device's `config.txt`.
- Follow the installed `$unihiker-k10-platformio` skill for K10 API lookup, toolchain setup, USB upload, serial monitoring, display refresh, AI model partitions, and offline workshop support.

## Required context

Resolve only inputs needed by the requested interaction:

- Wi-Fi SSID and password for the network shared by K10 and WIAnode;
- WIAnode IP shown after pressing `WKUP`;
- confirmed WIAnode port, module, SKU, and configured mode;
- which K10 input or output is involved;
- source and destination ranges, smoothing, threshold, rate limit, and fail-safe behavior.

Keep Wi-Fi credentials in `include/secrets.h`, which the template excludes from Git. Never repeat them in summaries, serial output, screenshots, or generated reports.

## Workflow

1. Detect an existing PlatformIO project from `platformio.ini`. If none exists, copy `assets/template/wianode-k10/` into a new project directory. Do not create Arduino CLI or MicroPython files.
2. Preserve the K10 PlatformIO environment from the template: DFRobot platform, `unihiker_k10` board, Arduino framework, USB CDC flags, and `Model=None` for ordinary Wi-Fi/MQTT projects.
3. Copy `include/secrets.example.h` to `include/secrets.h` and fill only the supplied Wi-Fi and WIAnode values. Do not commit the populated file.
4. Build a sensor-only tracer bullet first: connect Wi-Fi, connect MQTT with a unique client ID, subscribe to `topic_input`, parse strict JSON, print safe diagnostics, and update the K10 screen with partial redraws. For high-rate streams, measure broker publish rate separately from K10 receive and UI rates before tuning.
5. Add the requested mapping as the smallest visible change. Keep `mqtt.loop()` responsive, use bounded reconnect intervals, clamp mapped values, and rate-limit physical outputs. Coalesce high-rate sensor packets to the latest value instead of drawing every packet; when PubSubClient falls behind, drain a small bounded batch before rendering.
6. Build with `pio run -d <project>`. Fix all compile errors before upload. Use `pio device list` to resolve the board, then upload with `pio run -d <project> -t upload --upload-port <port>`.
7. Monitor at 115200 baud and verify Wi-Fi, MQTT, `topic_input` subscription, and at least one real packet when available. Never claim a physical output occurred without user observation.

## Hardware-output confirmation gate

The template sets `ENABLE_ACTUATOR_OUTPUT` to `false`. Leave it disabled for sensor display, logging, dashboards, and other read-only interactions.

Before generating or uploading firmware that can publish to `topic_output`, show:

- WIAnode IP and exact JSON payload or bounded payload rule;
- physical port, module, SKU, and configured mode;
- allowed range, clamp, publish rate, and stop/fail-safe behavior;
- the K10 event that will trigger the command.

Ask `确认生成并烧录上述 WIAnode 控制逻辑吗？` Only after affirmative confirmation may the project set `ENABLE_ACTUATOR_OUTPUT` to `true` and call the publish helper. Do not use retained actuator messages. A request to display sensor data or create a project does not authorize physical output.

## Completion evidence

Report separately:

- project path and PlatformIO environment;
- build result and upload port;
- Wi-Fi and MQTT connection state without credentials;
- observed `topic_input` keys and latest safe values;
- for reported latency, broker publish rate, K10 receive rate, and UI update rate as separate measurements;
- actuator logic enabled or disabled;
- commands actually published and physical results still `待用户确认`.

Do not claim completion from a successful compile alone. Upload and serial/MQTT verification are distinct evidence stages.
