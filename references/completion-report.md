# WIAnode configuration completion report

Use this structure after a guided configuration attempt. Report `完成`, `部分完成`, or `失败` accurately. Never include the Wi-Fi password.

## Result

- Status: `<完成 | 部分完成 | 失败>`
- Target device/volume: `<volume label and drive/path>`
- Configuration file: `<exact config.txt path>`
- Backup: `<exact backup path | not created and why>`

## Network

- SSID: `<SSID>`
- Password: `<已设置 | 未设置>`
- Addressing: `<DHCP | static IP, gateway, mask>`
- OLED IP: `<observed value | 待用户确认>`

## Interfaces

Always include every configured or attached interface. `SKU` is mandatory; write `未提供（待确认）` when it was not verified.

| Interface | SKU | Module | Config tag / detection | I2C address | Result |
| --- | --- | --- | --- | --- | --- |
| `<P1–P6/I2C>` | `<confirmed SKU or 未提供（待确认）>` | `<name>` | `<tag or auto-detect>` | `<address or —>` | `<validated / unconfirmed / error>` |

## Other settings

- Sending interval: `<value>`
- Status LED: `<on/off>`

## Verification

- Copy/write: `<success, not attempted, or error>`
- Config validation: `<pass, warning summary, or error summary>`
- Power cycle: `<completed | 待用户操作>`
- Indicator/OLED: `<observed status | 待用户确认>`
- MQTT: `<verified values/topics | not tested | error>`

## Next action

State only the remaining concrete action, if any—for example power-cycling, confirming an unverified SKU, reporting the LED color, or checking MQTT. Omit this section when nothing remains.
