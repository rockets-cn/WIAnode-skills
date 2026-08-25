# WIAnode sensor and actuator mapping

Read this file only when choosing port tags, checking an attachment, or interpreting an automatically detected I2C address. Source: [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), checked 2026-08-25.

## P1–P4 I/O

Use `input` for ordinary analog/digital modules that need no special library. Use the specialized tag where listed.

| Tag | Documented devices / examples |
| --- | --- |
| `input` | DFR0029 button, SEN0616 pressure, DFR0034 sound, DFR0026 light, SEN0508 liquid level, DFR0054 rotary angle, SEN0030 touch switch, SEN0185 Hall, SEN0019 IR obstacle, SEN0171 presence, SEN0307 analog ultrasonic, DFR0028 tilt, DFR1132 linear Hall, DFR0061 joystick |
| `dht11` | DFR0067 temperature/humidity |
| `ds18b20` | DFR0024 temperature |
| `ws2812` | FIT0656 RGB strip |

## P5–P6 servo

| Tag | Documented device |
| --- | --- |
| `servo180` | SER0006 180° servo |
| `servo300` | SER0053 9 g 300° clutch servo |
| `servo360` | SER0043 360° servo |

Do not assign servo tags to P1–P4 or I/O tags to P5–P6.

## Automatically detected I2C devices

Do not add these to `P1`–`P6`. Connect them to either I2C port and use the OLED interface page to confirm recognition.

| SKU | Data | Address |
| --- | --- | --- |
| SEN0626 | `FaceX`, `FaceY`, `GestureType` | `0x72` |
| SEN0561 | `Gesture` | `0x73` |
| SEN0304 | `Distance` | `0x11` |
| SEN0236 | `Temperature`, `Pressure`, `Altitude`, `Humidity` | `0x77` |
| SEN0212 | `R`, `G`, `B` | `0x29` |
| SEN0228 | `Lux` | `0x10` |
| SEN0224 | acceleration `x`, `y`, `z` | `0x18` |
| SEN0610 | `motion` | `0x2A` |
| SEN0636 | `UV` | `0x23` |
| SEN0514 | `TVOC`, `eCO2`, `AQI` | `0x52`, `0x53` |
| SEN0518 | `Heartbeat`, `SPO2` | `0x57` |
| SEN0536 | `CO2` | `0x62` |
| SEN0250 | acceleration and gyroscope axes | `0x69` |

The Wiki's general table names the SEN0212 color sensor, while one link label appears duplicated from another row. Use the SKU and observed I2C address—not the link label—as the identity check.
