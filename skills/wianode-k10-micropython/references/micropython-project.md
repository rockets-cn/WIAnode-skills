# K10 MicroPython project workflow

Read this reference when creating, uploading, monitoring, or troubleshooting a WIAnode project on UNIHIKER K10 with MicroPython. K10 MicroPython API details follow the installed `$unihiker-k10-micropython` skill and the official firmware docs; verified 2026-08-25 against the firmware 0.9.2 API reference.

## Template

Copy `assets/template/wianode-k10-micropython/` to the requested project directory. The project contains:

```text
wianode-k10-micropython/
├── .gitignore
├── main.py             # entry point; runs automatically on boot
├── secrets.example.py
└── (secrets.py         # created from the example; excluded from Git)
```

Copy `secrets.example.py` to `secrets.py`, then set the Wi-Fi SSID/password and the WIAnode IP from its OLED. `secrets.py` is intentionally ignored by Git. Do not place credentials in other source files, build logs, or REPL output.

The default project is read-only toward WIAnode: it subscribes to sensor data, displays discovered values, and keeps actuator publishing disabled.

## Firmware mode

K10 firmware is mutually exclusive: Arduino and MicroPython cannot run at the same time.

- If `mpremote` fails with "could not enter raw repl", the board is running Arduino firmware. Flash the MicroPython firmware first.
- Flashing procedure: hold `BOOT`, press `RST`, release `BOOT`, run the flash command (30–60 s), press `RST` to restart.
- Only `main.py` runs automatically after boot. Any other filename (e.g. `test.py`) must be imported or run through the REPL.
- V0.9.2 firmware cannot run AI features (`ai.*`, `asr.*`) and Wi-Fi at the same time. WIAnode projects need Wi-Fi, so keep AI out.
- Speech synthesis exists only in the Chinese MicroPython firmware. Confirm the board's firmware before using `asr.add_tts_data()` / `asr.start_tts()`.

## Commands

Use the installed `$unihiker-k10-micropython` skill's CLI when available:

```text
k10-micropython ports
k10-micropython doctor
k10-micropython upload-mp main.py
k10-micropython flash-mp
```

Plain `mpremote` equivalents:

```text
mpremote connect <port> cp main.py :main.py
mpremote connect <port> reset
mpremote connect <port> repl
```

Press `RST` on the board (or use `mpremote reset`) after uploading so `main.py` auto-runs, then read the REPL for the credential-free diagnostic lines.

## Runtime invariants

- Keep the main loop non-blocking: small `time.sleep_ms(...)` values, bounded Wi-Fi/MQTT reconnect intervals, and no tight reconnect loops.
- Do not render from the MQTT callback. Set a dirty flag with the parsed values; the main loop performs the partial redraw.
- Initialize the screen background once. Erase and redraw only changed rows or regions, then call `screen.show_draw()` once per visible change. Do not call `screen.clear()` or full-screen `screen.show_bg()` in the loop—it causes visible flicker.
- Use the field-tested MQTT design in the template: `umqtt.simple.MQTTClient` directly (NOT `k10_base.MqttClient`), two connections (`k10i-*` subscribes `topic_input`, `k10o-*` publishes and never subscribes), `check_msg()` drained from the main loop with idle-timeout errnos (11/116) treated as normal, and QoS 0 compact payloads. Re-subscribe on the input connection after every reconnect.
- Emit one credential-free diagnostic line per window (Wi-Fi, MQTT, packet count, UI frame count) instead of printing every high-rate packet.
- Only the template's `publish_wianode_command()` helper may publish; it refuses while `ENABLE_ACTUATOR_OUTPUT` is `False` or MQTT is disconnected.

## Verification sequence

1. The K10 runs MicroPython firmware (REPL reachable).
2. `main.py` is uploaded as the auto-run entry file and the board resets.
3. REPL shows Wi-Fi connected without printing credentials.
4. REPL shows MQTT connected and the `topic_input` callback registered.
5. A real WIAnode packet is parsed without a JSON error.
6. The K10 screen updates without full-screen redraw flicker (partial redraws).
7. For latency-sensitive dashboards, the latest value is displayed rather than a backlog; separate packet receive from UI update counts.
8. For output-enabled firmware, only the confirmed trigger and bounded payload publish; physical behavior remains user-observed evidence.
