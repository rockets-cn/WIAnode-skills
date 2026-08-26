# K10 PlatformIO project workflow

Read this reference when creating, building, uploading, monitoring, or troubleshooting a WIAnode project on UNIHIKER K10. The K10 platform configuration follows [DFRobot/platform-unihiker](https://github.com/DFRobot/platform-unihiker), checked 2026-08-25.

## Template

Copy `assets/template/wianode-k10/` to the requested project directory. The project contains:

```text
wianode-k10/
├── .gitignore
├── platformio.ini
├── include/
│   └── secrets.example.h
└── src/
    └── main.cpp
```

Copy `include/secrets.example.h` to `include/secrets.h`, then set the Wi-Fi SSID/password and the WIAnode IP from its OLED. `include/secrets.h` is intentionally ignored by Git. Do not place credentials in `platformio.ini`, source control, build logs, or serial messages.

The default project is read-only toward WIAnode: it subscribes to sensor data, displays the first value, and keeps actuator publishing disabled.

## PlatformIO environment

Keep this base configuration:

```ini
[env:unihiker]
platform = https://github.com/DFRobot/platform-unihiker.git
board = unihiker_k10
framework = arduino
monitor_speed = 115200
build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1
    -DARDUINO_USB_MODE=1
    -DModel=None
lib_deps =
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^7.4.3
```

[PubSubClient](https://github.com/knolleary/pubsubclient) supplies MQTT 3.1.1 over `WiFiClient`; [ArduinoJson](https://github.com/bblanchon/ArduinoJson) parses and serializes WIAnode payloads. Do not add a second MQTT or JSON implementation without a concrete requirement.

## Commands

Check the toolchain:

```text
pio --version
pio device list
```

Build:

```text
pio run -d <project-directory>
```

Upload by an explicitly resolved port:

```text
pio run -d <project-directory> -t upload --upload-port <port>
```

Monitor:

```text
pio device monitor -d <project-directory> --port <port> --baud 115200
```

On Windows or offline workshop installations, use the `$unihiker-k10-platformio` wrappers when available instead of assuming `pio` is on `PATH`.

## Runtime invariants

- Call `mqtt.loop()` frequently; do not block the main loop with long delays.
- Retry Wi-Fi and MQTT on bounded intervals instead of tight reconnect loops.
- Generate a unique MQTT client ID from the K10 MAC address so multiple boards do not disconnect one another.
- Increase the PubSubClient buffer before subscribing when payloads may exceed its default packet size. The template uses 1024 bytes.
- Initialize the K10 background once. Canvas screens update only changed text rows or regions and call `updateCanvas()` once per visible change. For polished or high-rate dashboards, read `lvgl-high-rate-dashboard.md` and create native LVGL objects once.
- At sending intervals below 100 ms, do not pair one `mqtt.loop()` call with one display flush. Coalesce to the latest validated value and use a bounded PubSubClient drain before rendering.
- Do not print every high-rate sensor packet. Count receive and UI updates over a time window and emit one credential-free diagnostic line instead.
- Keep `Model=None` unless the requested application genuinely uses K10 AI/voice features. Preserve factory model partitions if those features are introduced.

## Verification sequence

1. `pio run` exits successfully.
2. Upload exits successfully on the resolved K10 port.
3. Serial shows Wi-Fi connected without printing credentials.
4. Serial shows MQTT connected and subscribed to `topic_input`.
5. A real WIAnode packet is parsed without a JSON error.
6. The K10 screen updates without full-screen redraw flicker.
7. For latency-sensitive dashboards, K10 receive rate stays close to an independently measured broker rate and the UI displays the latest value rather than a backlog.
8. For output-enabled firmware, only the confirmed trigger and bounded payload publish; physical behavior remains user-observed evidence.
