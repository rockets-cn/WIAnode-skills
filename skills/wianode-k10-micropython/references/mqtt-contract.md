# WIAnode MQTT contract for K10 MicroPython

Read this reference before implementing connection, subscription, parsing, or publishing. Source: [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), checked 2026-08-25.

## Client implementation (field-tested 2026-08)

Use the firmware's `umqtt.simple.MQTTClient` directly, NOT `k10_base.MqttClient`. The wrapper reconnects in a tight loop and breaks QoS 1 PUBACK handling, which makes WIAnode outputs behave erratically. The reference dashboard uses two connections because the WIAnode only applies `topic_output` commands from connections that are not subscribed to `topic_input`:

```python
from umqtt.simple import MQTTClient

mqtt_in = MQTTClient("k10i-" + board_id, host, port=1883,
                     user="wianode", password="dfrobot", keepalive=30)
mqtt_in.connect()
mqtt_in.set_callback(on_input)
mqtt_in.subscribe(b"topic_input")   # receive only

mqtt_out = MQTTClient("k10o-" + board_id, host, port=1883,
                      user="wianode", password="dfrobot", keepalive=30)
mqtt_out.connect()                   # publish only; NEVER subscribes
mqtt_out.publish(b"topic_output", '{"p5":"270"}', qos=0)
```

If WIAnode stops applying output commands, power-cycle the WIAnode to clear its per-client session state before re-testing.

## Connection

- Broker: the WIAnode IP displayed after pressing `WKUP`.
- Port: `1883` unless the device explicitly uses another value.
- Username: `wianode`.
- Password: `dfrobot`.
- Subscribe topic: `topic_input`.
- Publish topic: `topic_output`.
- K10 and WIAnode must be on the same reachable Wi-Fi network.

Keep all connection values in the template's `secrets.py`. Never print passwords or include them in REPL output, screenshots, or reports. Derive the MQTT client ID from the board so multiple K10 boards do not disconnect one another:

```python
import binascii
import machine

client_id = "k10-" + binascii.hexlify(machine.unique_id()).decode()
```

## umqtt.simple API shape (field-tested)

The firmware ships `umqtt.simple`; use it instead of `k10_base.MqttClient` (see above). `WiFi` still comes from `k10_base`:

```python
from k10_base import WiFi
from umqtt.simple import MQTTClient

wifi = WiFi()
wifi.connect(ssid=WIFI_SSID, psd=WIFI_PASSWORD, timeout=50000)  # blocking
wifi.status()  # True when connected

client = MQTTClient(cid, WIANODE_HOST, port=1883,
                    user="wianode", password="dfrobot", keepalive=30)
client.connect()
client.sock.settimeout(0.005)      # keep check_msg non-blocking
client.set_callback(on_input)      # cb(topic, msg)
client.subscribe(b"topic_input")
client.check_msg()                 # call frequently from the main loop
client.publish(b"topic_output", '{"p5":"200"}', qos=0)
```

`check_msg()` raises `OSError` with errno 11/116 on idle timeouts — treat those as normal, not as a disconnect. There is no `connected()` method; track connection state with your own flag and recreate the client (with a fresh socket) on a real error. Keep `keepalive` above your idle period and send `ping()` if the loop can stall longer than the keepalive.

## Incoming sensor packets

WIAnode publishes a JSON object whose keys describe port, sensor type, and measurement:

```json
{"p1_input_val":1,"p2_dht11_temp":23,"p2_dht11_humi":88}
```

Parse with the firmware's `ujson` and reject malformed or non-object payloads:

```python
try:
    values = ujson.loads(msg)
except ValueError:
    print("MQTT JSON rejected")
    return
if not isinstance(values, dict):
    print("MQTT JSON rejected: not an object")
    return
```

Do not render inside the callback. Save the parsed values and set a dirty flag; the main loop performs the partial redraw. Discover the actual keys from real packets instead of inventing them. Treat missing updates as stale data; do not fabricate sensor values unless the user explicitly requests a labeled simulation mode.

### I2C module key discovery

I2C modules are auto-detected by WIAnode, and the docs do not guarantee their exact `topic_input` key names. For example, a SEN0228 lux sensor publishes its value under a key that contains `lux`, but the full name varies by firmware. When parsing, iterate the JSON object and match a case-insensitive key fragment instead of hard-coding a guessed key:

```python
def find_key_fragment(values, fragment):
    fragment_lower = fragment.lower()
    for key in values:
        if fragment_lower in key.lower():
            return key
    return None

lux_key = find_key_fragment(values, "lux")
if lux_key is not None:
    lux = values[lux_key]
```

Verify on the REPL that the fragment actually matched a key in the live stream before relying on it. Unknown I2C key names remain `waiting` on the dashboard rather than being fabricated.

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

- Re-subscribe to `topic_input` (and re-register the callback) after every successful MQTT reconnect.
- Keep the most recent validated sensor object and its receive flag.
- Surface MQTT connection state on the REPL when connection fails, but never include credentials.
- Stop publishing when Wi-Fi or MQTT is disconnected.
- Prefer a safe neutral command on an explicit user-designed stop event; do not invent a neutral position for servos or motors.
