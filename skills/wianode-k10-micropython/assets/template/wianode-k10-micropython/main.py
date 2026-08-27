# WIAnode x UNIHIKER K10 (MicroPython) - read-only sensor dashboard template.
#
# Field-tested on K10 v0.9.2 firmware (2026-08). This template uses the
# firmware's umqtt.simple client directly with TWO connections, because:
#   - k10_base.MqttClient reconnects in a tight loop and breaks QoS 1 PUBACK
#     handling, which makes WIAnode outputs behave erratically;
#   - the WIAnode only applies topic_output commands from connections that
#     are NOT subscribed to topic_input (and not from client IDs whose
#     persisted session ever subscribed).
# So k10i-* receives and k10o-* publishes; k10o-* never subscribes.
#
# Only main.py runs automatically on boot. Copy secrets.example.py to
# secrets.py and fill in real values before uploading, then reset the board.

import binascii
import json
import machine
import time

from k10_base import WiFi
from umqtt.simple import MQTTClient
from unihiker_k10 import screen

from secrets import (
    WIFI_SSID,
    WIFI_PASSWORD,
    WIANODE_HOST,
    WIANODE_PORT,
    WIANODE_MQTT_USERNAME,
    WIANODE_MQTT_PASSWORD,
)

TOPIC_INPUT = "topic_input"
TOPIC_OUTPUT = "topic_output"

# Keep False for read-only sensor projects. Enable only after the user confirms
# the exact WIAnode actuator, port, payload range, rate, and fail-safe behavior.
ENABLE_ACTUATOR_OUTPUT = False
SERVO_MIN_ANGLE = 30
SERVO_MAX_ANGLE = 270
# The knob value is quantized to 0.01 (~2.4 deg on a 240 deg span); a dead
# zone above one quantum stops ADC noise from oscillating the servo between
# adjacent angles.
SERVO_DEADZONE_DEG = 3
SERVO_INITIAL_ANGLE = 150
SERVO_PUBLISH_MIN_MS = 50

WIFI_RETRY_S = 5
MQTT_RETRY_S = 3
WIFI_CONNECT_TIMEOUT_MS = 50000
DIAGNOSTIC_LOG_S = 5
MAX_ROWS = 3
ROW_X = 10
ROW_W = 300
ROW_H = 30
STATUS_ROWS = 3  # rows 0..2 are status lines; sensor rows start at 3

SCREEN_BG = 0x000000
COLOR_TITLE = 0xFFFFFF
COLOR_OK = 0x00FF00
COLOR_WARN = 0xFFFF00
COLOR_ERROR = 0xFF0000

wifi = WiFi()
board_id = binascii.hexlify(machine.unique_id()).decode()
mqtt_in = None
mqtt_out = None
mqtt_in_connected = False
mqtt_out_connected = False

latest_values = None
values_received = False
rx_count = 0
ui_frames = 0
display_lines = ["", "", ""]
last_wifi_attempt = 0
last_mqtt_attempt = 0
last_diag_print = 0


def row_y(row):
    return 10 + row * 30


def draw_row(row, text, color):
    """Erase and redraw one row, then flush once (partial redraw)."""
    y = row_y(row)
    screen.draw_rect(x=ROW_X, y=y, w=ROW_W, h=ROW_H, bcolor=SCREEN_BG,
                     fcolor=SCREEN_BG)
    screen.draw_text(text=text[:26], x=ROW_X, y=y, font_size=24, color=color)
    screen.show_draw()


def connect_wifi():
    if wifi.status():
        return
    print("WiFi: connecting")
    draw_row(1, "WiFi: connecting", COLOR_WARN)
    wifi.connect(ssid=WIFI_SSID, psd=WIFI_PASSWORD,
                 timeout=WIFI_CONNECT_TIMEOUT_MS)
    if wifi.status():
        print("WiFi: connected")
        draw_row(1, "WiFi: connected", COLOR_OK)
    else:
        print("WiFi: connect failed")
        draw_row(1, "WiFi: failed", COLOR_ERROR)


def make_mqtt_client(cid):
    client = MQTTClient(cid, WIANODE_HOST, port=WIANODE_PORT,
                        user=WIANODE_MQTT_USERNAME,
                        password=WIANODE_MQTT_PASSWORD,
                        keepalive=30)
    client.connect()
    client.sock.settimeout(0.005)  # keep check_msg non-blocking
    return client


def connect_mqtt():
    global mqtt_in, mqtt_out, mqtt_in_connected, mqtt_out_connected
    if not wifi.status() or (mqtt_in_connected and mqtt_out_connected):
        return
    print("MQTT: connecting")
    draw_row(2, "MQTT: connecting", COLOR_WARN)
    try:
        if not mqtt_in_connected:
            if mqtt_in is None:
                mqtt_in = make_mqtt_client("k10i-" + board_id)
                mqtt_in.set_callback(on_input)
                mqtt_in.subscribe(b"topic_input")
            mqtt_in_connected = True
        if not mqtt_out_connected:
            if mqtt_out is None:
                # Publishing connection: NEVER subscribe to topic_input,
                # otherwise the WIAnode stops applying its commands.
                mqtt_out = make_mqtt_client("k10o-" + board_id)
            mqtt_out_connected = True
        print("MQTT: connected; subscribed to topic_input")
        draw_row(2, "MQTT: topic_input", COLOR_OK)
    except Exception as exc:
        mqtt_in = None
        mqtt_out = None
        mqtt_in_connected = False
        mqtt_out_connected = False
        print("MQTT: connect failed", type(exc).__name__)
        draw_row(2, "MQTT: retrying", COLOR_WARN)


def service_mqtt():
    """Drain incoming MQTT messages on both connections (like mqtt.loop()).
    Callbacks never render; they set flags only."""
    global mqtt_in, mqtt_out, mqtt_in_connected, mqtt_out_connected
    if mqtt_in is not None and mqtt_in_connected:
        try:
            mqtt_in.check_msg()
        except OSError as exc:
            if exc.errno not in (11, 116):  # EAGAIN/EWOULDBLOCK/ETIMEDOUT
                mqtt_in = None
                mqtt_in_connected = False
                print("MQTT: input connection lost; will reconnect")
        except Exception:
            mqtt_in = None
            mqtt_in_connected = False
            print("MQTT: input connection lost; will reconnect")
    if mqtt_out is not None and mqtt_out_connected:
        try:
            mqtt_out.check_msg()
        except OSError as exc:
            if exc.errno not in (11, 116):
                mqtt_out = None
                mqtt_out_connected = False
                print("MQTT: output connection lost; will reconnect")
        except Exception:
            mqtt_out = None
            mqtt_out_connected = False
            print("MQTT: output connection lost; will reconnect")


def on_input(topic, msg):
    """MQTT callback (umqtt.simple signature): parse and flag; never render."""
    global latest_values, values_received, rx_count
    try:
        values = json.loads(msg)
    except ValueError:
        print("MQTT JSON rejected")
        return
    if not isinstance(values, dict):
        print("MQTT JSON rejected: not an object")
        return
    latest_values = values
    values_received = True
    rx_count += 1


def render_if_needed(now):
    global display_lines, ui_frames
    if not values_received:
        return
    next_lines = []
    for key in latest_values:
        next_lines.append("{}={}".format(key, latest_values[key]))
    while len(next_lines) < MAX_ROWS:
        next_lines.append("")
    if next_lines == display_lines:
        return
    display_lines = next_lines
    for index in range(MAX_ROWS):
        y = row_y(index + STATUS_ROWS)
        screen.draw_rect(x=ROW_X, y=y, w=ROW_W, h=ROW_H, bcolor=SCREEN_BG,
                         fcolor=SCREEN_BG)
        screen.draw_text(text=display_lines[index][:26], x=ROW_X, y=y,
                         font_size=24, color=COLOR_OK)
    screen.show_draw()
    ui_frames += 1


def log_status_if_needed(now):
    global last_diag_print, rx_count, ui_frames
    if time.ticks_diff(now, last_diag_print) < DIAGNOSTIC_LOG_S * 1000:
        return
    last_diag_print = now
    print("Status WiFi={} MQTT={} RX={} UI={}".format(
        "connected" if wifi.status() else "offline",
        "connected" if (mqtt_in_connected and mqtt_out_connected)
        else "offline",
        rx_count,
        ui_frames,
    ))
    rx_count = 0
    ui_frames = 0


def compact_json(payload_dict):
    # json.dumps emits {"p5": "270"} (spaced); the WIAnode output path was
    # field-tested with compact {"p5":"270"}, so build it without spaces.
    parts = ['"%s":"%s"' % (key, payload_dict[key]) for key in payload_dict]
    return "{" + ",".join(parts) + "}"


def publish_wianode_command(payload_dict):
    if not ENABLE_ACTUATOR_OUTPUT:
        print("Actuator output is disabled")
        return False
    if not wifi.status() or not mqtt_out_connected or mqtt_out is None:
        return False
    try:
        # QoS 0 compact publish on the dedicated output connection, identical
        # to the field-tested PlatformIO version.
        mqtt_out.publish(b"topic_output", compact_json(payload_dict), qos=0)
        return True
    except Exception:
        return False


screen.init(dir=2)
screen.show_bg(color=SCREEN_BG)  # full background only during initialization
draw_row(0, "WIAnode + K10", COLOR_TITLE)

if WIFI_SSID == "YOUR_WIFI_SSID":
    draw_row(1, "Set secrets.py first", COLOR_ERROR)
    print("Configure secrets.py before running")
    while True:
        time.sleep(1)

while True:
    now = time.ticks_ms()
    if not wifi.status():
        if (last_wifi_attempt == 0 or
                time.ticks_diff(now, last_wifi_attempt) >= WIFI_RETRY_S * 1000):
            last_wifi_attempt = now
            connect_wifi()
    if wifi.status() and not (mqtt_in_connected and mqtt_out_connected):
        if (last_mqtt_attempt == 0 or
                time.ticks_diff(now, last_mqtt_attempt) >= MQTT_RETRY_S * 1000):
            last_mqtt_attempt = now
            connect_mqtt()
    service_mqtt()
    render_if_needed(now)
    log_status_if_needed(now)
    time.sleep_ms(2)
