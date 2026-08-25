# MQTT connection check

Read this file when connecting software to WIAnode or diagnosing a green device that is not sending/receiving expected data. Source: [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), checked 2026-08-25.

## Connection values

- Broker host: the IP shown on the WIAnode OLED after pressing `WKUP`.
- Computer and WIAnode must be on the same reachable network.
- Username: `wianode` according to the main MQTT and TouchDesigner sections.
- Password: `dfrobot`.
- Subscribe topic: `topic_input`.
- Publish topic: `topic_output`.

The Wiki's VVVV paragraph instead says username `mqtt`. Treat this as a documentation or firmware-version inconsistency: try `wianode` first and only test `mqtt` explicitly as a diagnostic fallback if authentication fails. Report which value worked.

## Payload shape

Incoming sensor data is a JSON object whose keys encode the port, device, and measurement, for example:

```json
{"p1_input_val": 1, "p2_dht11_temp": 23, "p2_dht11_humi": 88}
```

Publish actuator commands as a JSON object keyed by port. For a three-pixel WS2812 strip on P1:

```json
{"p1": "66 42 59 64 48 63 63 54 67"}
```

For a 300° servo on P5, first configure `P5: servo300`, then publish a value in the documented 0–300 range:

```json
{"p5": "200"}
```

The Wiki visually uses single quotes in some examples, but strict JSON uses double quotes. Prefer double quotes unless a specific client performs serialization itself.

If Mosquitto CLI tools are already installed, these read-only/explicit test commands are suitable after substituting the OLED IP:

```powershell
mosquitto_sub -h <WIAnode-IP> -u wianode -P dfrobot -t topic_input -v
mosquitto_pub -h <WIAnode-IP> -u wianode -P dfrobot -t topic_output -m '{"p5":"200"}'
```

Publishing moves hardware. Confirm the configured port and safe actuator range before running a publish test.
