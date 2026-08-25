# WIAnode MQTT contract for K10

Read this reference before implementing connection, subscription, parsing, or publishing. Source: [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), checked 2026-08-25.

## Connection

- Broker: the WIAnode IP displayed after pressing `WKUP`.
- Port: `1883` unless the device explicitly uses another value.
- Username: `wianode`.
- Password: `dfrobot`.
- Subscribe topic: `topic_input`.
- Publish topic: `topic_output`.
- K10 and WIAnode must be on the same reachable Wi-Fi network.

Store all connection values in `include/secrets.h`. Do not print passwords. Use the K10 MAC address in the MQTT client ID.

## Incoming sensor packets

WIAnode publishes a JSON object whose keys describe port, sensor type, and measurement:

```json
{"p1_input_val":1,"p2_dht11_temp":23,"p2_dht11_humi":88}
```

Parse with `deserializeJson(doc, payload, length)`. Reject malformed or non-object payloads. Discover the actual keys from real packets instead of inventing them. Treat missing updates as stale data; do not fabricate sensor values unless the user explicitly requests a labeled simulation mode.

## Outgoing actuator packets

Serialize strict JSON and publish to `topic_output` with retained messages disabled.

Examples:

```json
{"p5":"200"}
```

```json
{"p1":"66 42 59 64 48 63 63 54 67"}
```

The first example targets a P5 actuator such as a configured 300° servo. The second represents three WS2812 pixels as nine space-separated RGB integers.

Publishing can move hardware. Apply the confirmation gate in `SKILL.md`, clamp every value, and rate-limit continuous control. Do not infer mechanical safety from only the protocol's numeric range.

## Resilience

- Subscribe again after every successful MQTT reconnect.
- Keep the most recent validated sensor object and its receive timestamp.
- Surface MQTT state codes on serial when connection fails, but never include credentials.
- Stop publishing when Wi-Fi or MQTT is disconnected.
- Prefer a safe neutral command on an explicit user-designed stop event; do not invent a neutral position for servos or motors.
