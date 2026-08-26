#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "secrets.h"
#include "unihiker_k10.h"

namespace {

constexpr char TOPIC_INPUT[] = "topic_input";
constexpr char TOPIC_OUTPUT[] = "topic_output";

// Keep false for read-only sensor projects. Enable only after the user confirms
// the exact WIAnode actuator, port, payload range, rate, and fail-safe
// behavior.
constexpr bool ENABLE_ACTUATOR_OUTPUT = false;

constexpr uint32_t SCREEN_BACKGROUND = 0x000000;
constexpr uint8_t MAX_MEASUREMENTS = 3;
constexpr uint8_t MQTT_DRAIN_LIMIT = 8;
constexpr unsigned long WIFI_RETRY_MS = 5000;
constexpr unsigned long MQTT_RETRY_MS = 3000;
constexpr unsigned long UI_IDLE_MS = 5;
constexpr unsigned long DIAGNOSTIC_LOG_MS = 5000;

UNIHIKER_K10 k10;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

unsigned long lastWifiAttempt = 0;
unsigned long lastMqttAttempt = 0;
unsigned long lastUiRefresh = 0;
unsigned long lastDiagnosticLog = 0;
unsigned long mqttPacketsSinceLog = 0;
unsigned long uiFramesSinceLog = 0;
String measurementLines[MAX_MEASUREMENTS];
bool measurementsDirty = false;

String padLine(const String &text) {
  String output = text.substring(0, 28);
  while (output.length() < 28) {
    output += ' ';
  }
  return output;
}

void drawRow(uint8_t row, const String &text, uint32_t color) {
  k10.canvas->canvasText(padLine(text), row, color);
  k10.canvas->updateCanvas();
}

void renderMeasurementsIfNeeded() {
  if (!measurementsDirty || millis() - lastUiRefresh < UI_IDLE_MS) {
    return;
  }
  measurementsDirty = false;

  for (uint8_t index = 0; index < MAX_MEASUREMENTS; ++index) {
    k10.canvas->canvasText(padLine(measurementLines[index]), index + 3,
                           0x00FF00);
  }
  k10.canvas->updateCanvas();
  lastUiRefresh = millis();
  ++uiFramesSinceLog;
}

void onMqttMessage(char *topic, uint8_t *payload, unsigned int length) {
  if (strcmp(topic, TOPIC_INPUT) != 0) {
    return;
  }

  JsonDocument document;
  const DeserializationError error = deserializeJson(document, payload, length);
  if (error || !document.is<JsonObject>()) {
    Serial.printf("MQTT JSON rejected: %s\n", error.c_str());
    return;
  }

  ++mqttPacketsSinceLog;
  const JsonObjectConst values = document.as<JsonObjectConst>();
  String nextLines[MAX_MEASUREMENTS];
  uint8_t index = 0;
  for (JsonPairConst item : values) {
    String value;
    serializeJson(item.value(), value);
    nextLines[index] = String(item.key().c_str()) + "=" + value;
    if (++index >= MAX_MEASUREMENTS) {
      break;
    }
  }
  while (index < MAX_MEASUREMENTS) {
    nextLines[index++] = "";
  }

  bool changed = false;
  for (uint8_t line = 0; line < MAX_MEASUREMENTS; ++line) {
    if (measurementLines[line] != nextLines[line]) {
      measurementLines[line] = nextLines[line];
      changed = true;
    }
  }
  measurementsDirty = measurementsDirty || changed;
}

void connectWifiIfNeeded() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  const unsigned long now = millis();
  if (lastWifiAttempt != 0 && now - lastWifiAttempt < WIFI_RETRY_MS) {
    return;
  }
  lastWifiAttempt = now;

  drawRow(1, "WiFi: connecting", 0xFFFF00);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

String mqttClientId() {
  String clientId = "k10-" + WiFi.macAddress();
  clientId.replace(":", "");
  return clientId;
}

void connectMqttIfNeeded() {
  if (WiFi.status() != WL_CONNECTED || mqtt.connected()) {
    return;
  }

  const unsigned long now = millis();
  if (lastMqttAttempt != 0 && now - lastMqttAttempt < MQTT_RETRY_MS) {
    return;
  }
  lastMqttAttempt = now;

  if (mqtt.connect(mqttClientId().c_str(), WIANODE_MQTT_USERNAME,
                   WIANODE_MQTT_PASSWORD)) {
    mqtt.subscribe(TOPIC_INPUT);
    drawRow(1, "WiFi: connected", 0x00FF00);
    drawRow(2, "MQTT: topic_input", 0x00FF00);
    Serial.println("MQTT connected; subscribed to topic_input");
  } else {
    Serial.printf("MQTT connect failed: state=%d\n", mqtt.state());
    drawRow(2, "MQTT: retrying", 0xFFFF00);
  }
}

void serviceMqtt() {
  for (uint8_t packet = 0;
       packet < MQTT_DRAIN_LIMIT && mqtt.connected(); ++packet) {
    mqtt.loop();
  }
}

void logRuntimeStatusIfNeeded() {
  const unsigned long now = millis();
  const unsigned long elapsed = now - lastDiagnosticLog;
  if (elapsed < DIAGNOSTIC_LOG_MS) {
    return;
  }

  const double rxHz = mqttPacketsSinceLog * 1000.0 / elapsed;
  const double uiHz = uiFramesSinceLog * 1000.0 / elapsed;
  lastDiagnosticLog = now;
  mqttPacketsSinceLog = 0;
  uiFramesSinceLog = 0;
  Serial.printf("Status WiFi=%s MQTT=%s RX=%.1fHz UI=%.1fHz\n",
                WiFi.status() == WL_CONNECTED ? "connected" : "offline",
                mqtt.connected() ? "connected" : "offline", rxHz, uiHz);
}

bool publishWianodeCommand(const JsonDocument &command) {
  if (!ENABLE_ACTUATOR_OUTPUT) {
    Serial.println("Actuator output is disabled");
    return false;
  }
  if (!mqtt.connected()) {
    return false;
  }

  char payload[256];
  const size_t length = serializeJson(command, payload, sizeof(payload));
  if (length == 0 || length >= sizeof(payload)) {
    return false;
  }
  return mqtt.publish(TOPIC_OUTPUT, reinterpret_cast<uint8_t *>(payload),
                      length, false);
}

} // namespace

void setup() {
  Serial.begin(115200);

  k10.begin();
  k10.initScreen(2);
  k10.creatCanvas();
  k10.setScreenBackground(SCREEN_BACKGROUND);
  drawRow(0, "WIAnode + K10", 0xFFFFFF);

  if (strcmp(WIFI_SSID, "YOUR_WIFI_SSID") == 0) {
    drawRow(1, "Set include/secrets.h", 0xFF0000);
    Serial.println("Configure include/secrets.h before running");
    while (true) {
      delay(1000);
    }
  }

  WiFi.mode(WIFI_STA);
  mqtt.setServer(WIANODE_HOST, WIANODE_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(1024);
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(3);
  connectWifiIfNeeded();
}

void loop() {
  connectWifiIfNeeded();
  connectMqttIfNeeded();
  serviceMqtt();
  renderMeasurementsIfNeeded();
  logRuntimeStatusIfNeeded();
  delay(1);
}
