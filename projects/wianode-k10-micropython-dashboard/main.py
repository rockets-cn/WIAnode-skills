# WIAnode x UNIHIKER K10 - MicroPython dashboard.
#
# MicroPython port of projects/wianode-k10-dashboard (PlatformIO + LVGL).
# Same hardware and MQTT contract:
#   - P1 knob (DFR0054)  -> P5 servo (SER0053, servo300): 30-270 deg, 1 deg dead zone
#   - P2 sound module     (key "p2_input_val")
#   - SEN0228 lux sensor  (I2C; key discovered from real packets by "lux" fragment)
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
ROTARY_KEY = "p1_input_val"
SOUND_KEY = "p2_input_val"

# P5 300-degree clutch servo driven by the P1 rotary knob. The mapping,
# range, dead zone, and rate were confirmed by the user (same mapping as the
# PlatformIO version, reconfirmed for this MicroPython firmware).
ENABLE_ACTUATOR_OUTPUT = True
SERVO_MIN_ANGLE = 30
SERVO_MAX_ANGLE = 270
# The knob value is quantized to 0.01 (~2.4 deg on the 240 deg span). A dead
# zone slightly above one quantum stops sub-quantum ADC jitter from
# oscillating the servo between adjacent angles.
SERVO_DEADZONE_DEG = 3
SERVO_INITIAL_ANGLE = 150

WIFI_RETRY_S = 5
MQTT_RETRY_S = 3
WIFI_CONNECT_TIMEOUT_MS = 50000
UI_REFRESH_MS = 33
DIAGNOSTIC_LOG_S = 5
CHART_POINTS = 32
# Screen SPI work blocks the main thread, so keep chart redraws throttled
# to keep the loop (and therefore MQTT check_msg draining) responsive.
CHART_REDRAW_MS = 500
SERVO_PUBLISH_MIN_MS = 50

# Colors (same palette as the LVGL version).
BACKGROUND = 0x07111F
CARD = 0x101D30
CARD_BORDER = 0x243752
MUTED = 0x8EA3BF
WHITE = 0xF4F8FF
GREEN = 0x24E5A3
BLUE = 0x4CA7FF
YELLOW = 0xFFC857
RED = 0xFF5D73
CHART_BG = 0x0A1424
HEADER = 0x133E7C
TRACK = 0x1C2B41
GRID = CARD_BORDER

# Chart plot area (inside the LUX TREND panel).
CHART_X0 = 20
CHART_X1 = 219
CHART_Y0 = 88
CHART_Y1 = 146

wifi = WiFi()
# MQTT uses the firmware's umqtt.simple client directly. The k10_base
# MqttClient wrapper was observed reconnecting in a tight loop and breaking
# QoS 1 PUBACK handling. Two separate connections are used because the
# WIAnode only applies topic_output commands from clients that have no
# topic_input subscription (nor a persisted session that subscribed):
#   - k10i-* : subscribes topic_input, receives sensor data.
#   - k10o-* : never subscribes, publishes topic_output (servo etc).
board_id = binascii.hexlify(machine.unique_id()).decode()
mqtt_in = None
mqtt_out = None
mqtt_in_connected = False
mqtt_out_connected = False


class SensorState:
    def __init__(self, label, color, range_min=None, range_max=None):
        self.label = label
        self.color = color
        self.value = 0.0
        self.observed_min = 0.0
        self.observed_max = 0.0
        self.range_min = range_min
        self.range_max = range_max
        self.seen = False
        self.dirty = False


# The knob publishes a normalized 0..1 value, so its percent bar and servo
# mapping use the fixed range instead of adapting to observed extremes.
rotary = SensorState("P1 KNOB -> P5", GREEN, range_min=0.0, range_max=1.0)
sound = SensorState("P2 SOUND", BLUE)
lux = SensorState("SEN0228 LUX", YELLOW)

chart_values = [None] * CHART_POINTS
chart_head = 0
chart_count = 0

desired_servo_angle = SERVO_INITIAL_ANGLE
last_wifi_attempt = 0
last_mqtt_attempt = 0
last_ui_refresh = 0
last_diag_print = 0
last_chart_redraw = 0
last_servo_publish = 0
rx_count = 0
ui_frames = 0


def text_width(text, font_size):
    # Approximate ASCII glyph width; used only for centering short labels.
    return int(len(text) * font_size * 0.48)


def draw_card(x, y, w, h):
    screen.draw_rect(x=x, y=y, w=w, h=h, bcolor=CARD_BORDER, fcolor=CARD)


def render_status(status_text, color):
    screen.draw_rect(x=174, y=8, w=54, h=30, bcolor=color, fcolor=color)
    x = 174 + (54 - text_width(status_text, 18)) // 2
    screen.draw_text(text=status_text, x=x, y=13, font_size=18, color=BACKGROUND)


def render_ip_line(text):
    screen.draw_rect(x=10, y=48, w=150, h=20, bcolor=BACKGROUND, fcolor=BACKGROUND)
    screen.draw_text(text=text, x=12, y=48, font_size=18, color=MUTED)


def render_sys_line(text, color, y):
    screen.draw_rect(x=131, y=y, w=96, h=20, bcolor=CARD, fcolor=CARD)
    screen.draw_text(text=text, x=133, y=y, font_size=18, color=color)


def render_servo_line():
    render_sys_line("P5 {} deg".format(desired_servo_angle), WHITE, 298)


def render_sensor_value(sensor, x, y):
    screen.draw_rect(x=x, y=y, w=90, h=24, bcolor=CARD, fcolor=CARD)
    text = "waiting" if not sensor.seen else "{:.0f}".format(sensor.value)
    screen.draw_text(text=text, x=x, y=y, font_size=24, color=sensor.color)


def sensor_percent(sensor):
    if sensor.range_min is not None:
        span = sensor.range_max - sensor.range_min
        value = sensor.value
    else:
        span = sensor.observed_max - sensor.observed_min
        value = sensor.value - sensor.observed_min
    if span < 1e-6:
        return 50
    ratio = value / span
    if ratio < 0.0:
        ratio = 0.0
    if ratio > 1.0:
        ratio = 1.0
    return int(ratio * 100.0)


def render_sensor_bar(sensor, x, y):
    screen.draw_rect(x=x, y=y, w=89, h=8, bcolor=TRACK, fcolor=TRACK)
    fill_w = int(89 * sensor_percent(sensor) / 100)
    if fill_w > 0:
        screen.draw_rect(x=x, y=y, w=fill_w, h=8, bcolor=sensor.color,
                         fcolor=sensor.color)


def add_chart_point(value):
    global chart_head, chart_count
    chart_values[chart_head] = value
    chart_head = (chart_head + 1) % CHART_POINTS
    if chart_count < CHART_POINTS:
        chart_count += 1


def render_chart():
    screen.draw_rect(x=CHART_X0, y=CHART_Y0, w=CHART_X1 - CHART_X0 + 1,
                     h=CHART_Y1 - CHART_Y0 + 1, bcolor=CHART_BG, fcolor=CHART_BG)
    for g in (1, 2):
        gy = CHART_Y1 - int((CHART_Y1 - CHART_Y0) * g / 3)
        screen.draw_line(x0=CHART_X0, y0=gy, x1=CHART_X1, y1=gy, color=GRID)
    if chart_count < 2:
        return
    n = chart_count
    prev_x = None
    prev_y = None
    for i in range(n):
        idx = (chart_head - n + i) % CHART_POINTS
        value = chart_values[idx]
        if value is None:
            prev_x = None
            prev_y = None
            continue
        x = CHART_X0 + int(i * (CHART_X1 - CHART_X0) / (CHART_POINTS - 1))
        y = CHART_Y1 - int(value / 100.0 * (CHART_Y1 - CHART_Y0))
        if prev_x is not None:
            screen.draw_line(x0=prev_x, y0=prev_y, x1=x, y1=y, color=YELLOW)
        prev_x = x
        prev_y = y


def init_ui():
    screen.init(dir=2)
    screen.show_bg(color=BACKGROUND)  # full background only during init

    screen.draw_rect(x=0, y=0, w=240, h=46, bcolor=HEADER, fcolor=HEADER)
    screen.draw_text(text="WIAnode LIVE", x=12, y=4, font_size=24, color=WHITE)
    screen.draw_text(text="K10 DASHBOARD", x=12, y=28, font_size=18,
                     color=0xC6E7F4)
    render_status("START", YELLOW)
    render_ip_line("K10 IP  connecting...")

    draw_card(10, 62, 220, 90)
    screen.draw_text(text="LUX TREND (normalized)", x=22, y=70, font_size=18,
                     color=MUTED)
    render_chart()

    draw_card(10, 158, 105, 74)
    draw_card(125, 158, 105, 74)
    draw_card(10, 238, 105, 74)
    draw_card(125, 238, 105, 80)
    screen.draw_text(text=rotary.label, x=18, y=166, font_size=18, color=MUTED)
    screen.draw_text(text=lux.label, x=133, y=166, font_size=18, color=MUTED)
    screen.draw_text(text=sound.label, x=18, y=246, font_size=18, color=MUTED)
    screen.draw_text(text="SYSTEM", x=133, y=244, font_size=18, color=MUTED)
    render_sensor_value(rotary, 18, 188)
    render_sensor_value(lux, 133, 188)
    render_sensor_value(sound, 18, 268)
    render_sensor_bar(rotary, 18, 214)
    render_sensor_bar(lux, 133, 214)
    render_sensor_bar(sound, 18, 294)
    render_servo_line()
    screen.show_draw()


def apply_connection_ui(status_text, status_color, ip_text):
    render_status(status_text, status_color)
    render_ip_line(ip_text)
    wifi_ok = wifi.status()
    mqtt_ok = mqtt_in_connected and mqtt_out_connected
    render_sys_line("WiFi on" if wifi_ok else "WiFi off",
                    GREEN if wifi_ok else RED, 264)
    render_sys_line("MQTT on" if mqtt_ok else "MQTT off",
                    GREEN if mqtt_ok else RED, 284)


def wifi_ip():
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        if wlan and wlan.isconnected():
            return wlan.ifconfig()[0]
    except Exception:
        pass
    return "connected"


def connect_wifi():
    if wifi.status():
        return
    print("WiFi: connecting")
    apply_connection_ui("WIFI", YELLOW, "K10 IP  connecting...")
    screen.show_draw()
    wifi.connect(ssid=WIFI_SSID, psd=WIFI_PASSWORD,
                 timeout=WIFI_CONNECT_TIMEOUT_MS)
    if wifi.status():
        print("WiFi: connected")
        apply_connection_ui("WIFI", YELLOW, "K10 IP  " + wifi_ip())
    else:
        print("WiFi: connect failed")
        apply_connection_ui("RETRY", RED, "K10 IP  connecting...")
    screen.show_draw()


def make_mqtt_client(cid):
    client = MQTTClient(cid, WIANODE_HOST, port=WIANODE_PORT,
                        user=WIANODE_MQTT_USERNAME,
                        password=WIANODE_MQTT_PASSWORD,
                        keepalive=30)
    client.connect()
    client.sock.settimeout(0.005)
    return client


def connect_mqtt():
    global mqtt_in, mqtt_out, mqtt_in_connected, mqtt_out_connected
    if not wifi.status() or (mqtt_in_connected and mqtt_out_connected):
        return
    print("MQTT: connecting")
    ip_text = "K10 IP  " + wifi_ip()
    apply_connection_ui("MQTT", YELLOW, ip_text)
    screen.show_draw()
    try:
        if not mqtt_in_connected:
            if mqtt_in is None:
                mqtt_in = make_mqtt_client("k10i-" + board_id)
                mqtt_in.set_callback(on_input)
                mqtt_in.subscribe(b"topic_input")
            mqtt_in_connected = True
        if not mqtt_out_connected:
            if mqtt_out is None:
                mqtt_out = make_mqtt_client("k10o-" + board_id)
            mqtt_out_connected = True
        print("MQTT: connected; subscribed to topic_input")
        apply_connection_ui("LIVE", GREEN, ip_text)
    except Exception as exc:
        mqtt_in = None
        mqtt_out = None
        mqtt_in_connected = False
        mqtt_out_connected = False
        print("MQTT: connect failed", type(exc).__name__)
        apply_connection_ui("RETRY", RED, ip_text)
    screen.show_draw()


def service_mqtt():
    """Drain incoming MQTT messages on both connections (like mqtt.loop()
    in the PlatformIO version). Callbacks never render; they set flags."""
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


def read_numeric(values, key):
    if key not in values:
        return None
    value = values[key]
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def read_lux_value(values):
    for key in values:
        if "lux" in key.lower():
            value = read_numeric(values, key)
            if value is not None:
                return value
    return None


def update_sensor(sensor, value):
    changed = (not sensor.seen) or abs(sensor.value - value) > 1e-6
    sensor.value = value
    if not sensor.seen:
        sensor.observed_min = value
        sensor.observed_max = value
        sensor.seen = True
    else:
        if value < sensor.observed_min:
            sensor.observed_min = value
        if value > sensor.observed_max:
            sensor.observed_max = value
    sensor.dirty = sensor.dirty or changed


def on_input(topic, msg):
    """MQTT callback (umqtt.simple signature): parse and flag; never render."""
    global rx_count
    try:
        values = json.loads(msg)
    except ValueError:
        print("MQTT JSON rejected")
        return
    if not isinstance(values, dict):
        print("MQTT JSON rejected: not an object")
        return
    rx_count += 1
    value = read_numeric(values, ROTARY_KEY)
    if value is not None:
        update_sensor(rotary, value)
    value = read_numeric(values, SOUND_KEY)
    if value is not None:
        update_sensor(sound, value)
    value = read_lux_value(values)
    if value is not None:
        update_sensor(lux, value)


def render_if_needed(now):
    global last_ui_refresh, ui_frames, last_chart_redraw
    if time.ticks_diff(now, last_ui_refresh) < UI_REFRESH_MS:
        return
    if not (rotary.dirty or sound.dirty or lux.dirty):
        return
    last_ui_refresh = now
    if rotary.dirty:
        rotary.dirty = False
        render_sensor_value(rotary, 18, 188)
        render_sensor_bar(rotary, 18, 214)
    if lux.dirty:
        lux.dirty = False
        render_sensor_value(lux, 133, 188)
        render_sensor_bar(lux, 133, 214)
        if lux.observed_max > 1.0:
            normalized = min(100.0, lux.value / lux.observed_max * 100.0)
        else:
            normalized = 0.0
        add_chart_point(normalized)
        if time.ticks_diff(now, last_chart_redraw) >= CHART_REDRAW_MS:
            last_chart_redraw = now
            render_chart()
    if sound.dirty:
        sound.dirty = False
        render_sensor_value(sound, 18, 268)
        render_sensor_bar(sound, 18, 294)
    screen.show_draw()
    ui_frames += 1


def compact_json(payload_dict):
    # MicroPython json.dumps emits {"p5": "270"} (spaced). The WIAnode
    # output path was field-tested with ArduinoJson's compact {"p5":"270"},
    # so build the payload without spaces.
    parts = ['"%s":"%s"' % (key, payload_dict[key]) for key in payload_dict]
    return "{" + ",".join(parts) + "}"


def publish_wianode_command(payload_dict):
    if not ENABLE_ACTUATOR_OUTPUT:
        print("Actuator output is disabled")
        return False
    if not wifi.status() or not mqtt_out_connected or mqtt_out is None:
        return False
    content = compact_json(payload_dict)
    try:
        # QoS 0 compact publish on the dedicated output connection (which
        # never subscribes to topic_input), identical to the field-tested
        # PlatformIO version.
        mqtt_out.publish(b"topic_output", content, qos=0)
        return True
    except Exception:
        return False


def map_rotary_to_servo_angle():
    # The knob value is normalized 0..1 by WIAnode and quantized to 0.01;
    # snap to that quantum so ADC noise inside one quantum maps identically.
    value = round(rotary.value, 2)
    if value < 0.0:
        value = 0.0
    if value > 1.0:
        value = 1.0
    return SERVO_MIN_ANGLE + int(round(value * (SERVO_MAX_ANGLE - SERVO_MIN_ANGLE)))


def handle_knob_servo():
    global desired_servo_angle, last_servo_publish
    if not ENABLE_ACTUATOR_OUTPUT or not rotary.seen:
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, last_servo_publish) < SERVO_PUBLISH_MIN_MS:
        return
    target_angle = map_rotary_to_servo_angle()
    if abs(target_angle - desired_servo_angle) < SERVO_DEADZONE_DEG:
        return
    if publish_wianode_command({"p5": str(target_angle)}):
        desired_servo_angle = target_angle
        last_servo_publish = now
        render_servo_line()
        screen.show_draw()
        print("P5 angle published: {} (knob)".format(desired_servo_angle))
    else:
        print("P5 command not published: connection unavailable")


def log_status_if_needed(now):
    global last_diag_print, rx_count, ui_frames
    if time.ticks_diff(now, last_diag_print) < DIAGNOSTIC_LOG_S * 1000:
        return
    last_diag_print = now
    print("Status WiFi={} IP={} MQTT={} RX={} UI={} P1={} P2={} LUX={} SERVO={}".format(
        "connected" if wifi.status() else "offline",
        wifi_ip(),
        "connected" if (mqtt_in_connected and mqtt_out_connected) else "offline",
        rx_count,
        ui_frames,
        "{:.0f}".format(rotary.value) if rotary.seen else "waiting",
        "{:.0f}".format(sound.value) if sound.seen else "waiting",
        "{:.0f}".format(lux.value) if lux.seen else "waiting",
        desired_servo_angle,
    ))
    rx_count = 0
    ui_frames = 0


init_ui()

if WIFI_SSID == "YOUR_WIFI_SSID":
    render_ip_line("Set secrets.py first")
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
    handle_knob_servo()
    log_status_if_needed(now)
    time.sleep_ms(2)
