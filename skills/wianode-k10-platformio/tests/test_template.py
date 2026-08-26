from __future__ import annotations

import configparser
import unittest
from pathlib import Path


TEMPLATE = Path(__file__).parents[1] / "assets" / "template" / "wianode-k10"


class WianodeK10TemplateTests(unittest.TestCase):
    def test_platformio_environment_and_dependencies(self) -> None:
        config = configparser.ConfigParser()
        config.read(TEMPLATE / "platformio.ini")
        environment = config["env:unihiker"]

        self.assertEqual(environment["board"], "unihiker_k10")
        self.assertEqual(environment["framework"], "arduino")
        self.assertIn("DFRobot/platform-unihiker", environment["platform"])
        self.assertIn("PubSubClient@^2.8", environment["lib_deps"])
        self.assertIn("ArduinoJson@^7.4.3", environment["lib_deps"])
        self.assertIn("-DModel=None", environment["build_flags"])

    def test_template_is_sensor_only_and_credential_safe(self) -> None:
        source = (TEMPLATE / "src" / "main.cpp").read_text(encoding="utf-8")
        ignore = (TEMPLATE / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("ENABLE_ACTUATOR_OUTPUT = false", source)
        self.assertIn('TOPIC_INPUT[] = "topic_input"', source)
        self.assertIn('TOPIC_OUTPUT[] = "topic_output"', source)
        self.assertIn("mqtt.loop()", source)
        self.assertIn("MQTT_DRAIN_LIMIT = 8", source)
        self.assertIn("packet < MQTT_DRAIN_LIMIT && mqtt.connected()", source)
        self.assertIn("renderMeasurementsIfNeeded()", source)
        self.assertIn("measurementsDirty = measurementsDirty || changed", source)
        self.assertIn("lastUiRefresh = millis()", source)
        self.assertIn("DIAGNOSTIC_LOG_MS = 5000", source)
        callback = source.split("void onMqttMessage", 1)[1].split(
            "void connectWifiIfNeeded", 1
        )[0]
        self.assertNotIn("drawRow(", callback)
        self.assertNotIn("updateCanvas()", callback)
        self.assertNotIn("Serial.println(measurement)", callback)
        self.assertIn("include/secrets.h", ignore)
        self.assertFalse((TEMPLATE / "include" / "secrets.h").exists())

    def test_secret_example_requires_wifi_and_wianode_values(self) -> None:
        example = (TEMPLATE / "include" / "secrets.example.h").read_text(
            encoding="utf-8"
        )

        self.assertIn("YOUR_WIFI_SSID", example)
        self.assertIn("YOUR_WIFI_PASSWORD", example)
        self.assertIn("WIANODE_HOST", example)
        self.assertIn("WIANODE_MQTT_USERNAME", example)
        self.assertIn("WIANODE_MQTT_PASSWORD", example)


if __name__ == "__main__":
    unittest.main()
