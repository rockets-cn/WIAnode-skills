#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <lvgl.h>

#include "secrets.h"
#include "unihiker_k10.h"

extern SemaphoreHandle_t xLvglMutex;

namespace {

constexpr char TOPIC_INPUT[] = "topic_input";
constexpr char TOPIC_OUTPUT[] = "topic_output";
constexpr char ROTARY_KEY[] = "p1_input_val";
constexpr char SOUND_KEY[] = "p2_input_val";

// P5 300-degree clutch servo controlled by the P1 rotary knob. The mapping,
// range, dead zone, and rate were confirmed by the user before output was
// enabled.
constexpr bool ENABLE_ACTUATOR_OUTPUT = true;
constexpr int SERVO_MIN_ANGLE = 30;
constexpr int SERVO_MAX_ANGLE = 270;
constexpr int SERVO_DEADZONE_DEG = 1;
constexpr int SERVO_INITIAL_ANGLE = 150;

constexpr uint32_t COLOR_BACKGROUND = 0x07111F;
constexpr uint32_t COLOR_CARD = 0x101D30;
constexpr uint32_t COLOR_CARD_BORDER = 0x243752;
constexpr uint32_t COLOR_MUTED = 0x8EA3BF;
constexpr uint32_t COLOR_WHITE = 0xF4F8FF;
constexpr uint32_t COLOR_GREEN = 0x24E5A3;
constexpr uint32_t COLOR_GREEN_DARK = 0x0A7D69;
constexpr uint32_t COLOR_BLUE = 0x4CA7FF;
constexpr uint32_t COLOR_BLUE_DARK = 0x315DE8;
constexpr uint32_t COLOR_YELLOW = 0xFFC857;
constexpr uint32_t COLOR_RED = 0xFF5D73;
constexpr uint32_t COLOR_CHART_BG = 0x0A1424;

constexpr unsigned long WIFI_RETRY_MS = 5000;
constexpr unsigned long MQTT_RETRY_MS = 3000;
// Leave a short MQTT-processing window after each physical display flush.
constexpr unsigned long UI_REFRESH_MS = 5;
constexpr unsigned long DIAGNOSTIC_LOG_MS = 5000;
constexpr uint32_t CHART_POINTS = 64;
constexpr double CHART_MAX = 100.0;

struct SensorState {
  SensorState(const char *labelValue, uint32_t colorValue,
              uint32_t gradientValue)
      : label(labelValue), color(colorValue), gradientColor(gradientValue) {}

  const char *label;
  uint32_t color;
  uint32_t gradientColor;
  double value = 0.0;
  double observedMin = 0.0;
  double observedMax = 0.0;
  bool seen = false;
  bool dirty = false;
};

struct SensorWidgets {
  lv_obj_t *valueLabel = nullptr;
  lv_obj_t *bar = nullptr;
};

struct DashboardWidgets {
  lv_obj_t *statusPill = nullptr;
  lv_obj_t *statusLabel = nullptr;
  lv_obj_t *ipLabel = nullptr;
  SensorWidgets rotary;
  SensorWidgets sound;
  SensorWidgets lux;
  lv_obj_t *chart = nullptr;
  lv_chart_series_t *luxSeries = nullptr;
  lv_obj_t *sysWifiLabel = nullptr;
  lv_obj_t *sysMqttLabel = nullptr;
  lv_obj_t *servoValueLabel = nullptr;
};

UNIHIKER_K10 k10;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
SensorState rotary{"P1 KNOB -> P5", COLOR_GREEN, COLOR_GREEN_DARK};
SensorState sound{"P2 SOUND", COLOR_BLUE, COLOR_BLUE_DARK};
SensorState lux{"SEN0228 LUX", COLOR_YELLOW, COLOR_YELLOW};
DashboardWidgets ui;

unsigned long lastWifiAttempt = 0;
unsigned long lastMqttAttempt = 0;
unsigned long lastUiRefresh = 0;
unsigned long lastDiagnosticLog = 0;
unsigned long mqttPacketsSinceLog = 0;
unsigned long uiFramesSinceLog = 0;
int desiredServoAngle = SERVO_INITIAL_ANGLE;

void lockLvgl() { xSemaphoreTake(xLvglMutex, portMAX_DELAY); }

void unlockLvgl() { xSemaphoreGive(xLvglMutex); }

void setObjectColor(lv_obj_t *object, uint32_t color, lv_style_selector_t part) {
  lv_obj_set_style_bg_color(object, lv_color_hex(color), part);
  lv_obj_set_style_bg_opa(object, LV_OPA_COVER, part);
}

lv_obj_t *createLabel(lv_obj_t *parent, const char *text, int x, int y,
                      uint32_t color) {
  lv_obj_t *label = lv_label_create(parent);
  lv_label_set_text(label, text);
  lv_obj_set_pos(label, x, y);
  lv_obj_set_style_text_color(label, lv_color_hex(color), 0);
  return label;
}

lv_obj_t *createPanel(lv_obj_t *parent, int x, int y, int width, int height) {
  lv_obj_t *panel = lv_obj_create(parent);
  lv_obj_remove_style_all(panel);
  lv_obj_set_pos(panel, x, y);
  lv_obj_set_size(panel, width, height);
  lv_obj_set_style_radius(panel, 12, 0);
  setObjectColor(panel, COLOR_CARD, 0);
  lv_obj_set_style_border_color(panel, lv_color_hex(COLOR_CARD_BORDER), 0);
  lv_obj_set_style_border_width(panel, 1, 0);
  lv_obj_set_style_shadow_color(panel, lv_color_hex(0x000000), 0);
  lv_obj_set_style_shadow_opa(panel, LV_OPA_30, 0);
  lv_obj_set_style_shadow_width(panel, 8, 0);
  lv_obj_clear_flag(panel, LV_OBJ_FLAG_SCROLLABLE);
  return panel;
}

SensorWidgets createCompactCard(lv_obj_t *screen, const SensorState &sensor,
                                int x, int y) {
  SensorWidgets widgets;
  lv_obj_t *card = createPanel(screen, x, y, 105, 74);
  createLabel(card, sensor.label, 8, 6, COLOR_MUTED);

  widgets.valueLabel = createLabel(card, "waiting", x == 10 ? 60 : 46, 6,
                                   sensor.color);
  lv_obj_set_width(widgets.valueLabel, 50);
  lv_obj_set_style_text_align(widgets.valueLabel, LV_TEXT_ALIGN_RIGHT, 0);

  widgets.bar = lv_bar_create(card);
  lv_obj_set_pos(widgets.bar, 8, 46);
  lv_obj_set_size(widgets.bar, 89, 12);
  lv_bar_set_range(widgets.bar, 0, 100);
  lv_bar_set_value(widgets.bar, 0, LV_ANIM_OFF);
  lv_obj_set_style_radius(widgets.bar, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  setObjectColor(widgets.bar, 0x1C2B41, LV_PART_MAIN);
  lv_obj_set_style_radius(widgets.bar, LV_RADIUS_CIRCLE, LV_PART_INDICATOR);
  setObjectColor(widgets.bar, sensor.color, LV_PART_INDICATOR);
  lv_obj_set_style_bg_grad_color(widgets.bar,
                                 lv_color_hex(sensor.gradientColor),
                                 LV_PART_INDICATOR);
  lv_obj_set_style_bg_grad_dir(widgets.bar, LV_GRAD_DIR_HOR,
                               LV_PART_INDICATOR);
  return widgets;
}

void initializeUi() {
  lockLvgl();
  lv_obj_t *screen = lv_scr_act();
  lv_obj_clean(screen);
  lv_obj_clear_flag(screen, LV_OBJ_FLAG_SCROLLABLE);
  setObjectColor(screen, COLOR_BACKGROUND, 0);
  lv_obj_set_style_pad_all(screen, 0, 0);

  lv_obj_t *header = lv_obj_create(screen);
  lv_obj_remove_style_all(header);
  lv_obj_set_pos(header, 0, 0);
  lv_obj_set_size(header, 240, 46);
  setObjectColor(header, 0x133E7C, 0);
  lv_obj_set_style_bg_grad_color(header, lv_color_hex(0x087C8C), 0);
  lv_obj_set_style_bg_grad_dir(header, LV_GRAD_DIR_HOR, 0);
  lv_obj_clear_flag(header, LV_OBJ_FLAG_SCROLLABLE);

  createLabel(header, "WIAnode LIVE", 12, 6, COLOR_WHITE);
  createLabel(header, "K10 SENSOR DASHBOARD", 12, 25, 0xC6E7F4);

  ui.statusPill = lv_obj_create(header);
  lv_obj_remove_style_all(ui.statusPill);
  lv_obj_set_pos(ui.statusPill, 174, 9);
  lv_obj_set_size(ui.statusPill, 54, 27);
  lv_obj_set_style_radius(ui.statusPill, LV_RADIUS_CIRCLE, 0);
  setObjectColor(ui.statusPill, COLOR_YELLOW, 0);
  ui.statusLabel = lv_label_create(ui.statusPill);
  lv_label_set_text(ui.statusLabel, "START");
  lv_obj_set_style_text_color(ui.statusLabel, lv_color_hex(COLOR_BACKGROUND),
                              0);
  lv_obj_center(ui.statusLabel);

  ui.ipLabel = createLabel(screen, "K10 IP  connecting...", 12, 50,
                           COLOR_MUTED);

  // Lux trend chart panel.
  lv_obj_t *chartPanel = createPanel(screen, 10, 62, 220, 90);
  createLabel(chartPanel, "LUX TREND  (normalized)", 12, 8, COLOR_MUTED);
  ui.chart = lv_chart_create(chartPanel);
  lv_obj_set_pos(ui.chart, 10, 24);
  lv_obj_set_size(ui.chart, 200, 60);
  lv_chart_set_type(ui.chart, LV_CHART_TYPE_LINE);
  lv_chart_set_point_count(ui.chart, CHART_POINTS);
  lv_chart_set_range(ui.chart, LV_CHART_AXIS_PRIMARY_Y, 0, CHART_MAX);
  lv_chart_set_update_mode(ui.chart, LV_CHART_UPDATE_MODE_SHIFT);
  lv_chart_set_div_line_count(ui.chart, 4, 8);
  setObjectColor(ui.chart, COLOR_CHART_BG, LV_PART_MAIN);
  lv_obj_set_style_line_color(ui.chart, lv_color_hex(COLOR_CARD_BORDER),
                              LV_PART_MAIN);
  lv_obj_set_style_line_width(ui.chart, 1, LV_PART_MAIN);
  lv_obj_set_style_radius(ui.chart, 0, LV_PART_MAIN);
  ui.luxSeries =
      lv_chart_add_series(ui.chart, lv_color_hex(COLOR_YELLOW),
                          LV_CHART_AXIS_PRIMARY_Y);

  // Sensor cards row 1.
  ui.rotary = createCompactCard(screen, rotary, 10, 158);
  ui.lux = createCompactCard(screen, lux, 125, 158);

  // Sensor cards row 2.
  ui.sound = createCompactCard(screen, sound, 10, 238);

  // System status card.
  lv_obj_t *sysCard = createPanel(screen, 125, 238, 105, 74);
  createLabel(sysCard, "SYSTEM", 8, 6, COLOR_MUTED);
  ui.sysWifiLabel = createLabel(sysCard, "WiFi --", 8, 26, COLOR_MUTED);
  ui.sysMqttLabel = createLabel(sysCard, "MQTT --", 8, 42, COLOR_MUTED);
  ui.servoValueLabel = createLabel(sysCard, "P5 150 deg", 8, 58, COLOR_WHITE);

  lv_task_handler();
  unlockLvgl();
}

void setConnectionUi(const char *status, uint32_t color,
                     const String &ipText) {
  lockLvgl();
  lv_label_set_text(ui.statusLabel, status);
  setObjectColor(ui.statusPill, color, 0);
  lv_obj_set_style_text_color(ui.statusLabel, lv_color_hex(COLOR_BACKGROUND),
                              0);
  lv_label_set_text(ui.ipLabel, ipText.c_str());
  lv_obj_set_style_text_color(
      ui.sysWifiLabel,
      lv_color_hex(WiFi.status() == WL_CONNECTED ? COLOR_GREEN : COLOR_RED),
      0);
  lv_label_set_text(ui.sysWifiLabel,
                    WiFi.status() == WL_CONNECTED ? "WiFi on" : "WiFi off");
  lv_obj_set_style_text_color(
      ui.sysMqttLabel,
      lv_color_hex(mqtt.connected() ? COLOR_GREEN : COLOR_RED), 0);
  lv_label_set_text(ui.sysMqttLabel,
                    mqtt.connected() ? "MQTT on" : "MQTT off");
  lv_task_handler();
  unlockLvgl();
}

void updateSensor(SensorState &sensor, double value) {
  const bool valueChanged =
      !sensor.seen || fabs(sensor.value - value) > 0.000001;
  sensor.value = value;
  if (!sensor.seen) {
    sensor.observedMin = value;
    sensor.observedMax = value;
    sensor.seen = true;
  } else {
    sensor.observedMin = min(sensor.observedMin, value);
    sensor.observedMax = max(sensor.observedMax, value);
  }
  sensor.dirty = sensor.dirty || valueChanged;
}

bool readNumeric(JsonObjectConst values, const char *key, double &result) {
  JsonVariantConst value = values[key];
  if (!(value.is<int>() || value.is<unsigned int>() || value.is<long>() ||
        value.is<unsigned long>() || value.is<float>() || value.is<double>())) {
    return false;
  }
  result = value.as<double>();
  return isfinite(result);
}

// I2C SEN0228 publishes its measurement under a key that contains "lux".
// Discover it from the real packet instead of hard-coding an unverified name.
bool readLuxValue(JsonObjectConst values, double &result) {
  for (JsonPairConst pair : values) {
    const char *key = pair.key().c_str();
    if (!key) {
      continue;
    }
    bool found = false;
    for (const char *p = key; *p; ++p) {
      if ((*p == 'l' || *p == 'L') && (p[1] == 'u' || p[1] == 'U') &&
          (p[2] == 'x' || p[2] == 'X')) {
        found = true;
        break;
      }
    }
    if (found && readNumeric(values, key, result)) {
      return true;
    }
  }
  return false;
}

int sensorPercent(const SensorState &sensor) {
  const double span = sensor.observedMax - sensor.observedMin;
  if (span < 0.000001) {
    return 50;
  }
  const double ratio =
      constrain((sensor.value - sensor.observedMin) / span, 0.0, 1.0);
  return static_cast<int>(ratio * 100.0);
}

void updateSensorWidgets(const SensorState &sensor,
                         const SensorWidgets &widgets) {
  char valueText[24];
  snprintf(valueText, sizeof(valueText), "%.0f", sensor.value);
  lv_label_set_text(widgets.valueLabel, valueText);
  lv_bar_set_value(widgets.bar, sensorPercent(sensor), LV_ANIM_OFF);
}

void updateLuxChart(const SensorState &sensor) {
  double normalized = 0.0;
  if (sensor.observedMax > 1.0) {
    normalized = constrain(sensor.value / sensor.observedMax * CHART_MAX, 0.0,
                           CHART_MAX);
  }
  lv_chart_set_next_value(ui.chart, ui.luxSeries,
                          static_cast<lv_coord_t>(normalized));
  lv_chart_refresh(ui.chart);
}

void renderSensorsIfNeeded() {
  const unsigned long now = millis();
  if (now - lastUiRefresh < UI_REFRESH_MS ||
      (!rotary.dirty && !sound.dirty && !lux.dirty)) {
    return;
  }
  lockLvgl();
  if (rotary.dirty) {
    rotary.dirty = false;
    updateSensorWidgets(rotary, ui.rotary);
  }
  if (sound.dirty) {
    sound.dirty = false;
    updateSensorWidgets(sound, ui.sound);
  }
  if (lux.dirty) {
    lux.dirty = false;
    updateSensorWidgets(lux, ui.lux);
    updateLuxChart(lux);
  }
  lv_task_handler();
  unlockLvgl();
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
  double value = 0.0;
  if (readNumeric(values, ROTARY_KEY, value)) {
    updateSensor(rotary, value);
  }
  if (readNumeric(values, SOUND_KEY, value)) {
    updateSensor(sound, value);
  }
  if (readLuxValue(values, value)) {
    updateSensor(lux, value);
  }
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
  setConnectionUi("WIFI", COLOR_YELLOW, "K10 IP  connecting...");
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

  const String ipText = "K10 IP  " + WiFi.localIP().toString();
  setConnectionUi("MQTT", COLOR_YELLOW, ipText);
  if (mqtt.connect(mqttClientId().c_str(), WIANODE_MQTT_USERNAME,
                   WIANODE_MQTT_PASSWORD)) {
    mqtt.subscribe(TOPIC_INPUT);
    setConnectionUi("LIVE", COLOR_GREEN, ipText);
    Serial.printf("WiFi connected; K10 IP=%s\n",
                  WiFi.localIP().toString().c_str());
    Serial.println("MQTT connected; subscribed to topic_input");
  } else {
    setConnectionUi("RETRY", COLOR_RED, ipText);
    Serial.printf("MQTT connect failed: state=%d\n", mqtt.state());
  }
}

void serviceMqtt() {
  // PubSubClient consumes at most one complete packet per loop() call. Drain a
  // short bounded batch so a display flush cannot leave old sensor packets
  // queued ahead of the newest values.
  for (uint8_t packet = 0; packet < 8 && mqtt.connected(); ++packet) {
    mqtt.loop();
  }
}

bool publishServoAngle(int angle) {
  if (!ENABLE_ACTUATOR_OUTPUT || WiFi.status() != WL_CONNECTED ||
      !mqtt.connected()) {
    return false;
  }

  JsonDocument command;
  command["p5"] = String(angle);
  char payload[64];
  const size_t length = serializeJson(command, payload, sizeof(payload));
  if (length == 0 || length >= sizeof(payload)) {
    return false;
  }
  return mqtt.publish(TOPIC_OUTPUT, reinterpret_cast<uint8_t *>(payload),
                      length, false);
}

void setServoUi() {
  char text[24];
  snprintf(text, sizeof(text), "P5 %d deg", desiredServoAngle);
  lockLvgl();
  lv_label_set_text(ui.servoValueLabel, text);
  lv_task_handler();
  unlockLvgl();
}

// Map the P1 rotary knob's observed dynamic range onto the confirmed
// mechanical servo range, then publish only when the mapped angle moved by at
// least the dead zone. Every knob change may publish (bounded by the 0.02 s
// WIAnode sending interval, i.e. up to ~50 Hz).
int mapRotaryToServoAngle() {
  const double span = rotary.observedMax - rotary.observedMin;
  if (span < 0.000001) {
    return SERVO_INITIAL_ANGLE;
  }
  const double ratio =
      constrain((rotary.value - rotary.observedMin) / span, 0.0, 1.0);
  return SERVO_MIN_ANGLE +
         static_cast<int>(round(ratio * (SERVO_MAX_ANGLE - SERVO_MIN_ANGLE)));
}

void handleKnobServoControl() {
  if (!ENABLE_ACTUATOR_OUTPUT || !rotary.seen) {
    return;
  }

  // Evaluate the knob directly every loop: the UI renderer consumes the
  // dirty flag first, so a separate "rotary changed" marker would be cleared
  // before this function runs. Comparing the mapped angle against the last
  // published angle gives the same dead-zone behavior without shared state.
  const int targetAngle = mapRotaryToServoAngle();
  if (abs(targetAngle - desiredServoAngle) < SERVO_DEADZONE_DEG) {
    return;
  }

  if (publishServoAngle(targetAngle)) {
    desiredServoAngle = targetAngle;
    setServoUi();
    Serial.printf("P5 angle published: %d (knob)\n", desiredServoAngle);
  } else {
    Serial.println("P5 command not published: connection unavailable");
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

  Serial.printf(
      "Status WiFi=%s IP=%s MQTT=%s RX=%.1fHz UI=%.1fHz P1=%s P2=%s LUX=%s "
      "SERVO=%d\n",
      WiFi.status() == WL_CONNECTED ? "connected" : "offline",
      WiFi.localIP().toString().c_str(),
      mqtt.connected() ? "connected" : "offline", rxHz, uiHz,
      rotary.seen ? String(rotary.value, 0).c_str() : "waiting",
      sound.seen ? String(sound.value, 0).c_str() : "waiting",
      lux.seen ? String(lux.value, 0).c_str() : "waiting", desiredServoAngle);
}

} // namespace

void setup() {
  Serial.begin(115200);

  k10.begin();
  k10.initScreen(2);
  initializeUi();

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
  renderSensorsIfNeeded();
  handleKnobServoControl();
  logRuntimeStatusIfNeeded();
  delay(1);
}
