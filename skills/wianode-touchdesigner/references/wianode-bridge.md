# WIAnode MQTT bridge in TouchDesigner

Read this reference when creating, inspecting, or repairing the WIAnode data connection. Sources: [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), [TouchDesigner MQTT Client DAT](https://docs.derivative.ca/MQTT_Client_DAT), and [mqttclientDAT class](https://docs.derivative.ca/MqttclientDAT_Class), checked 2026-08-25.

## Connection contract

- Broker host: the IP displayed by WIAnode after pressing `WKUP`.
- Broker URI: `tcp://<WIAnode-IP>:1883` unless the device or project explicitly uses another port.
- Username: `wianode`.
- Password: `dfrobot`.
- Subscribe topic: `topic_input`.
- Publish topic: `topic_output`.
- The computer and WIAnode must be on the same reachable network.

The DFRobot Wiki has one inconsistent VVVV example using username `mqtt`. Use `wianode` first. Test `mqtt` only as an explicit authentication diagnostic and report the credential variant that worked; never switch silently.

## Prefer or create

First inspect the project for the official WIAnode component or an existing MQTT Client DAT. Reuse it when its broker and topics match. If neither exists, create a dedicated Base COMP—normally `/project1/wianode_bridge`—containing:

```text
wianode_bridge
├── mqtt                 MQTT Client DAT
├── mqtt_callbacks       Text DAT used as the MQTT callbacks DAT
└── sensor_values        Table DAT: first column `key`, second column `value`
```

Create nodes with `create_td_node`, then inspect them with `get_td_node_parameters` before setting version-sensitive parameter names. Configure the MQTT DAT's network address, username, password, callbacks DAT, reconnect behavior, and Active state. Do not return or print the password.

The callbacks DAT should implement this behavior:

```python
import json


def onConnect(dat):
    dat.subscribe('topic_input')


def onConnectFailure(dat, msg):
    return


def onConnectionLost(dat, msg):
    return


def onSubscribe(dat):
    return


def onSubscribeFailure(dat, msg):
    return


def onUnsubscribe(dat):
    return


def onUnsubscribeFailure(dat, msg):
    return


def onPublish(dat):
    return


def onMessage(dat, topic, payload, qos, retained, dup):
    if topic != 'topic_input':
        return
    raw = payload.decode('utf-8') if isinstance(payload, (bytes, bytearray)) else str(payload)
    try:
        message = json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return
    if not isinstance(message, dict):
        return

    table = dat.parent().op('sensor_values')
    if table is None:
        return
    if table.numRows == 0:
        table.appendRow(['key', 'value'])
    for key, value in message.items():
        if table.row(str(key)):
            table[str(key), 'value'] = value
        else:
            table.appendRow([str(key), value])
```

Use the MCP server's `execute_python_script` only to set the Text DAT contents or perform connection operations that cannot be expressed through node parameters. Return paths and connection state, not credentials or full project dumps.

## Sensor packets

WIAnode publishes a JSON object whose keys encode port, device type, and measurement, for example:

```json
{"p1_input_val": 1, "p2_dht11_temp": 23, "p2_dht11_humi": 88}
```

Discover actual keys from a live packet rather than inventing them. Preserve numeric values as numbers. When input is stale or absent, do not fabricate fallback sensor data unless the user explicitly asks for a simulation mode and it is visibly labeled.

## Actuator publish

The MQTT Client DAT methods are:

```python
mqtt.subscribe('topic_input')
mqtt.publish('topic_output', payload_bytes, qos=0, retain=False)
```

Serialize strict JSON with double quotes and UTF-8 bytes:

```python
import json

command = {'p5': '200'}
payload = json.dumps(command, separators=(',', ':')).encode('utf-8')
op('/project1/wianode_bridge/mqtt').publish(
    'topic_output', payload, qos=0, retain=False
)
result = {'topic': 'topic_output', 'payload': command}
```

This script is an execution template, not standing authorization. Apply the hardware-output confirmation gate in `SKILL.md` immediately before sending it.
