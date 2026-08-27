from __future__ import annotations

import unittest
from pathlib import Path


PROJECT = Path(__file__).parents[1]


class WianodeK10MicropythonDashboardTests(unittest.TestCase):
    def test_main_compiles(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        compile(source, str(PROJECT / "main.py"), "exec")

    def test_topics_and_sensor_keys(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        self.assertIn('TOPIC_INPUT = "topic_input"', source)
        self.assertIn('TOPIC_OUTPUT = "topic_output"', source)
        self.assertIn('ROTARY_KEY = "p1_input_val"', source)
        self.assertIn('SOUND_KEY = "p2_input_val"', source)
        self.assertIn('"lux" in key.lower()', source)

    def test_uses_firmware_mqtt_api_and_secrets(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        self.assertIn("from k10_base import WiFi", source)
        self.assertIn("from umqtt.simple import MQTTClient", source)
        self.assertIn("from unihiker_k10 import screen", source)
        self.assertIn("from secrets import", source)
        # K10 v0.9.2 firmware is MicroPython >= 1.21: json, not ujson.
        self.assertIn("import json", source)
        self.assertNotIn("import ujson", source)
        self.assertNotIn("ujson.", source)
        self.assertIn('mqtt_in.subscribe(b"topic_input")', source)
        self.assertIn("mqtt_in.set_callback(on_input)", source)
        self.assertIn("board_id = binascii.hexlify(", source)
        self.assertIn('"k10i-" + board_id', source)
        self.assertIn('"k10o-" + board_id', source)

    def test_actuator_mapping_is_confirmation_gated(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        self.assertIn("ENABLE_ACTUATOR_OUTPUT", source)
        self.assertIn("SERVO_MIN_ANGLE = 30", source)
        self.assertIn("SERVO_MAX_ANGLE = 270", source)
        self.assertIn("SERVO_DEADZONE_DEG = 3", source)
        self.assertIn("SERVO_INITIAL_ANGLE = 150", source)
        self.assertIn('{"p5": str(target_angle)}', source)
        helper = source.split("def publish_wianode_command", 1)[1]
        self.assertIn("ENABLE_ACTUATOR_OUTPUT", helper)
        self.assertIn("mqtt_out_connected", helper)
        self.assertIn("compact_json", helper)
        self.assertIn("mqtt_out.publish(b\"topic_output\"", helper)
        self.assertIn("qos=0", helper)

    def test_callback_does_not_render(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        callback = source.split("def on_input(topic, msg):", 1)[1].split(
            "def render_if_needed", 1
        )[0]
        self.assertNotIn("screen.", callback)
        self.assertNotIn("render_sensor", callback)

    def test_main_loop_and_renderer_use_partial_redraws_only(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        loop = source.split("while True:", 1)[1]
        renderer = source.split("def render_if_needed", 1)[1].split(
            "def publish_wianode_command", 1
        )[0]

        self.assertNotIn("screen.clear()", loop)
        self.assertNotIn("screen.show_bg(", loop)
        # The renderer delegates to per-region helpers and flushes once.
        self.assertIn("render_sensor_value(", renderer)
        self.assertIn("render_sensor_bar(", renderer)
        self.assertIn("render_chart()", renderer)
        self.assertEqual(renderer.count("screen.show_draw()"), 1)
        # The per-region helpers erase then redraw (partial redraws).
        self.assertIn("screen.draw_rect(", source)
        self.assertIn("screen.draw_text(", source)

    def test_lux_trend_chart_present(self) -> None:
        source = (PROJECT / "main.py").read_text(encoding="utf-8")
        self.assertIn("CHART_POINTS = 32", source)
        self.assertIn("CHART_REDRAW_MS = 500", source)
        self.assertIn("def render_chart", source)
        self.assertIn("screen.draw_line(", source)

    def test_secrets_are_ignored_and_example_has_placeholders(self) -> None:
        ignore = (PROJECT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("secrets.py", ignore)
        example = (PROJECT / "secrets.example.py").read_text(encoding="utf-8")
        self.assertIn("YOUR_WIFI_SSID", example)
        self.assertIn("YOUR_WIFI_PASSWORD", example)
        self.assertIn("WIANODE_HOST", example)
        self.assertIn("WIANODE_PORT", example)
        self.assertIn("WIANODE_MQTT_USERNAME", example)
        self.assertIn("WIANODE_MQTT_PASSWORD", example)


if __name__ == "__main__":
    unittest.main()
