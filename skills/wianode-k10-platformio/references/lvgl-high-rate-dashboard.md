# K10 LVGL dashboards and high-rate WIAnode streams

Read this reference when the K10 display should look polished, when WIAnode publishes faster than 10 Hz, or when values appear delayed even though MQTT is connected.

## Choose the display path

- Use the K10 Canvas wrapper for a small diagnostic screen or initial packet-key discovery.
- Prefer native LVGL objects for a finished dashboard: create labels, cards, status indicators, and bars once, then update only their properties.
- Do not create a Canvas behind a native LVGL dashboard. Both use the same screen, and the Canvas allocates a large additional buffer that the LVGL path does not need.

The bundled K10 framework used in the validated setup contains LVGL 8.3.10. Only Montserrat 14 is enabled by default, so verify font configuration before designing around larger built-in fonts.

## K10 LVGL ownership

Call `k10.begin()` and `k10.initScreen(2)` before using `lv_scr_act()`. The K10 library owns the display driver and exposes its mutex as `xLvglMutex`. In the validated framework version, direct LVGL access uses:

```cpp
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <lvgl.h>

extern SemaphoreHandle_t xLvglMutex;

void updateUi() {
  xSemaphoreTake(xLvglMutex, portMAX_DELAY);
  // Create or update LVGL objects here.
  lv_task_handler();
  xSemaphoreGive(xLvglMutex);
}
```

Lock every object creation and update. Never call LVGL or Canvas drawing functions from the MQTT callback; save validated values there and render from `loop()`. This mutex symbol is framework-specific, so confirm it still exists after a K10 framework upgrade and keep a Canvas fallback when portability matters.

## Avoid MQTT backlog

High-rate display delay is often a queueing problem, not just a low frame rate. PubSubClient processes at most one complete packet per `loop()` call. If a display flush takes longer than the WIAnode sending interval, one MQTT call followed by one draw causes old packets to accumulate.

Use three controls together:

1. The callback overwrites the stored sensor value and marks it dirty only when the value changes.
2. Drain a small bounded packet batch before rendering.
3. Render the newest stored value, then start the UI cooldown after the physical flush completes.

```cpp
constexpr uint8_t MQTT_DRAIN_LIMIT = 8;
constexpr unsigned long UI_IDLE_MS = 5;

void serviceMqtt() {
  for (uint8_t packet = 0;
       packet < MQTT_DRAIN_LIMIT && mqtt.connected(); ++packet) {
    mqtt.loop();
  }
}

void renderLatestIfDue() {
  if (!dirty || millis() - lastUiFlush < UI_IDLE_MS) {
    return;
  }
  // Update only changed labels/bars, with LV_ANIM_OFF for direct response.
  updateUi();
  dirty = false;
  lastUiFlush = millis();
}
```

The batch limit is a responsiveness bound, not a universal constant. Keep it small enough that buttons and reconnect logic remain responsive. Do not add a long blocking delay to create UI spacing.

## Measure the right rates

Report three rates separately when diagnosing latency:

- broker publish rate, measured with an independent read-only subscriber;
- K10 receive rate, counted in the validated MQTT callback;
- UI update rate, counted after an actual LVGL/Canvas flush.

Do not require UI FPS to equal the sensor rate. A useful design may receive 50 Hz, coalesce values, and draw the latest state at 15–20 FPS. What matters is that the screen shows current data instead of replaying a backlog.

One validated K10/WIAnode case measured 49.6 Hz at the broker. Drawing every packet limited K10 reception to about 19–21 Hz. Bounded draining and latest-value coalescing raised K10 reception to 49.8–50.1 Hz while the native LVGL dashboard updated changed regions at about 14–18.5 FPS. Treat these as diagnostic reference values, not guaranteed hardware limits.

## Dashboard construction

- Build the static hierarchy once: header, connection badge, K10 IP, sensor cards, labels, bars, and actuator status.
- Use `lv_bar_set_value(..., LV_ANIM_OFF)` when minimum latency matters. Animation can be added only when its intentional lag is acceptable.
- Use gradients, rounded cards, and status colors as static styles; do not reconstruct objects per packet.
- Preserve raw sensor values alongside normalized bars. If the hardware range is unknown, label bars as using an observed dynamic range instead of inventing a fixed full scale.
- Keep actuator publishing independent from UI refresh. A button edge may publish one confirmed command, but screen rendering must never generate actuator traffic.

## LVGL 8.3 chart notes

The bundled K10 framework ships LVGL 8.3.10, where the chart API differs from newer releases:

- Update a line series with `lv_chart_set_next_value(chart, series, value)`. `lv_chart_set_next_point` does not exist in 8.3.x and fails to compile; it appears only in later LVGL major versions.
- Build a scrolling window with `LV_CHART_UPDATE_MODE_SHIFT` and a bounded point count (e.g. 64), then call `lv_chart_refresh(chart)` after feeding each value.
- Set the Y range explicitly with `lv_chart_set_range(chart, LV_CHART_AXIS_PRIMARY_Y, 0, max)`.
- When the sensor's hardware scale is unknown (lux, ADC, etc.), normalize before plotting: `normalized = value / observedMax * chartMax`, clamped to the chart range. This keeps the trend visible without inventing a full scale and avoids large-value overflow of the `lv_coord_t` point type.
- Only Montserrat 14 is enabled by default, so keep chart titles short and do not design around larger built-in fonts.
- Feed the chart from `loop()` under the LVGL mutex, never from the MQTT callback; store the latest value in the sensor state and push it on the next render pass.
