from __future__ import annotations

import unittest
from pathlib import Path


TEMPLATE = (
    Path(__file__).parents[1]
    / "assets"
    / "template"
    / "wianode-k10-micropython"
)


class WianodeK10MicropythonTemplateTests(unittest.TestCase):
    def test_template_is_sensor_only_and_credential_safe(self) -> None:
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        ignore = (TEMPLATE / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("ENABLE_ACTUATOR_OUTPUT = False", source)
        self.assertIn('TOPIC_INPUT = "topic_input"', source)
        self.assertIn('TOPIC_OUTPUT = "topic_output"', source)
        # Field-tested MQTT design: umqtt.simple with two connections.
        self.assertIn("from k10_base import WiFi", source)
        self.assertIn("from umqtt.simple import MQTTClient", source)
        self.assertIn("from secrets import", source)
        self.assertIn('mqtt_in.subscribe(b"topic_input")', source)
        self.assertIn("mqtt_in.set_callback(on_input)", source)
        self.assertIn('make_mqtt_client("k10i-" + board_id)', source)
        self.assertIn('make_mqtt_client("k10o-" + board_id)', source)
        self.assertIn("secrets.py", ignore)
        self.assertFalse((TEMPLATE / "secrets.py").exists())

    def test_main_loop_and_renderer_use_partial_redraws_only(self) -> None:
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        loop = source.split("while True:", 1)[1]
        renderer = source.split("def render_if_needed", 1)[1].split(
            "def log_status_if_needed", 1
        )[0]

        # Full-screen refresh is allowed only during initialization.
        self.assertNotIn("screen.clear()", loop)
        self.assertNotIn("screen.show_bg(", loop)
        self.assertNotIn("screen.clear()", renderer)
        self.assertNotIn("screen.show_bg(", renderer)
        # Erase the row region, then draw, then flush exactly once.
        self.assertIn("screen.draw_rect(", renderer)
        self.assertIn("screen.draw_text(", renderer)
        self.assertEqual(renderer.count("screen.show_draw()"), 1)

    def test_callback_does_not_render(self) -> None:
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        callback = source.split("def on_input(topic, msg):", 1)[1].split(
            "def render_if_needed", 1
        )[0]

        self.assertNotIn("screen.", callback)
        self.assertNotIn("draw_row(", callback)

    def test_mqtt_layer_uses_field_tested_patterns(self) -> None:
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        self.assertIn("mqtt_out.publish(b\"topic_output\"", source)
        self.assertIn("qos=0", source)
        self.assertIn("compact_json", source)
        self.assertIn("client.sock.settimeout(0.005)", source)
        self.assertIn("exc.errno not in (11, 116)", source)
        # The broken wrapper must not be imported or instantiated (it may
        # only be mentioned in comments explaining why it is avoided).
        self.assertNotIn("from k10_base import WiFi, MqttClient", source)
        self.assertNotIn("MqttClient()", source)

    def test_publish_helper_is_confirmation_gated(self) -> None:
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        helper = source.split("def publish_wianode_command", 1)[1]

        self.assertIn("ENABLE_ACTUATOR_OUTPUT", helper)
        self.assertIn("mqtt_out_connected", helper)
        self.assertIn("compact_json", helper)
        self.assertIn("mqtt_out.publish(b\"topic_output\"", helper)
        self.assertIn("qos=0", helper)

    def test_json_module_is_json_not_ujson(self) -> None:
        # K10 v0.9.2 firmware is MicroPython >= 1.21, which renamed ujson to
        # json and kept no alias; import ujson raises ImportError at boot.
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        self.assertIn("import json", source)
        self.assertNotIn("import ujson", source)
        self.assertNotIn("ujson.", source)

    def test_servo_dead_zone_above_knob_quantum(self) -> None:
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        self.assertIn("SERVO_DEADZONE_DEG = 3", source)
        self.assertIn("SERVO_MIN_ANGLE = 30", source)
        self.assertIn("SERVO_MAX_ANGLE = 270", source)

    def test_secret_example_requires_wifi_and_wianode_values(self) -> None:
        example = (TEMPLATE / "secrets.example.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("YOUR_WIFI_SSID", example)
        self.assertIn("YOUR_WIFI_PASSWORD", example)
        self.assertIn("WIANODE_HOST", example)
        self.assertIn("WIANODE_PORT", example)
        self.assertIn("WIANODE_MQTT_USERNAME", example)
        self.assertIn("WIANODE_MQTT_PASSWORD", example)

    def test_main_py_compiles(self) -> None:
        # Syntax check on the host CPython, which accepts MicroPython syntax
        # that stays within the core language.
        source = (TEMPLATE / "main.py").read_text(encoding="utf-8")
        compile(source, str(TEMPLATE / "main.py"), "exec")


if __name__ == "__main__":
    unittest.main()
