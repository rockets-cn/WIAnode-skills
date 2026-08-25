---
name: wianode-config
description: Guide, configure, review, validate, and troubleshoot DFRobot WIAnode network, port, sensor, LED, sending-interval, and MQTT settings, including confirmation before device writes and completion reports with SKUs. Use for requests such as "我要配置 WIAnode", config.txt work, or connection diagnosis; do not use for unrelated DFRobot boards or firmware development.
---

# WIAnode configuration

Configure the device from its existing `config.txt` whenever possible. Preserve the file's comments, order, unknown keys, encoding, and line endings; change only the requested values. Never invent Wi-Fi credentials, static-network values, attached sensors, or a removable-drive path.

## Guided session

When the user only states an intent such as “我要配置 WIAnode”, begin a guided session instead of expecting them to know the configuration schema:

1. Tell them to connect WIAnode with a Type-C data cable and wait for its removable volume, attach the intended sensors/actuators, and note each module's printed SKU and port. Explain that I2C devices use the I2C connectors rather than P1–P6 tags.
2. Use read-only checks to look for a removable volume containing `config.txt`. If none is available, continue gathering settings while asking the user to connect the device. If several candidates exist, show the candidates and ask which one is WIAnode.
3. Collect only missing inputs in one concise intake: Wi-Fi SSID/password, DHCP or static IPv4 values, each port plus module name and SKU, sending interval, and LED state. Prefer DHCP, `0.02s`, and LED `on` only as clearly labeled suggestions—not assumed decisions.
4. Use [references/sensors.md](references/sensors.md) to map confirmed SKUs to tags or I2C addresses. If the user gives only a generic module name, suggest a likely documented SKU as **unconfirmed** and ask them to check the printed label. Never convert a guess into a confirmed SKU.

## Workflow and confirmation gate

1. Determine the requested outcome and collect only missing required inputs. Do not repeat a supplied Wi-Fi password in summaries or command output.
2. Read [references/config-format.md](references/config-format.md) before creating or editing a configuration. Read [references/sensors.md](references/sensors.md) only when mapping sensors or actuators. Read [references/mqtt.md](references/mqtt.md) only when connecting a client or diagnosing data flow.
3. If the device is connected as removable storage, locate candidates by the presence of `config.txt`; do not trust a fixed volume name. If multiple candidates exist, stop and ask which is WIAnode. Read the selected file and plan a timestamped backup at an exact, user-visible path, but do not create it before the confirmation gate.
4. Before every real device write, present a confirmation preview containing:
   - exact target volume and `config.txt` path;
   - exact backup destination;
   - SSID with password shown only as `<已设置>`, plus DHCP/static settings;
   - a table of port, module, SKU, resolved tag or I2C address, and any unconfirmed values;
   - sending interval, LED state, and validation warnings.
5. Ask: `确认按上述内容写入 <exact path> 吗？` Do not back up, edit, or copy until the user gives an affirmative response after seeing this preview. A general opening request such as “我要配置 WIAnode” is not write authorization.
6. After confirmation, create the announced backup, make only the approved changes, and run `python scripts/validate_config.py <path-to-config.txt>`. Resolve errors; explain warnings that are intentionally preserved. Stop after one failed write or validation attempt and report the failure instead of repeatedly overwriting the device.
7. Save the file, then tell the user to power-cycle WIAnode so the new configuration is applied. Verify the indicator and OLED before testing MQTT when those observations are available.
8. Finish with the structure in [references/completion-report.md](references/completion-report.md). Always include the SKU column; use `未提供（待确认）` rather than guessing. Report unavailable physical observations as `待用户确认`, not as successful.

## Safety and diagnosis

- Prefer DHCP unless the user specifically needs a static address and provides a compatible IP, gateway, and mask.
- Never overwrite a newly mounted drive merely because it is removable. Resolve the exact `config.txt`, retain a backup, and preserve any settings the user did not ask to change.
- Do not modify firmware as part of ordinary configuration. Firmware copying and power-cycle timing are separate, higher-risk operations.
- Yellow breathing means Wi-Fi information still needs configuration. Red breathing means saved but not connected: check credentials, 2.4 GHz availability, then power-cycle. Green means network connected.
- The official Wiki is internally inconsistent about the MQTT username. Use `wianode` first because the main MQTT and TouchDesigner sections agree on it; treat `mqtt` only as a firmware/version diagnostic fallback. Never silently switch credentials.

Authoritative source: [DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode).
