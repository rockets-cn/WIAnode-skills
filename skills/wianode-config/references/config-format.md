# WIAnode `config.txt`

Use this reference for any configuration draft, edit, or review. It summarizes the [official DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode), checked 2026-08-25.

## Application sequence

1. Connect WIAnode to the computer by a Type-C data cable.
2. Open the device's existing `config.txt` on the mounted removable volume.
3. Edit only the required values and save the file. Do not add quotes around values.
4. Power-cycle the device. A successful Wi-Fi connection shows an IP address on the OLED and changes the status indicator to green.

WIAnode requires a 2.4 GHz Wi-Fi network; a mixed 2.4/5 GHz network is also documented as supported. A 5 GHz-only network is not suitable.

## Documented template

Treat the file shipped by the device as the firmware-specific baseline. The following is a Wiki-based reconstruction for drafting or comparison, not a reason to discard firmware-specific comments, keys, or values:

```text
#WIFI SETTING
WiFi_Name:<SSID>
WiFi_Password:<PASSWORD>

#IP SETTING(Leave it blank for the default automatic address asignment)
Static_IP:
Gateway:
Subnet_Mask:

#I/O SETTING
P1:<input|dht11|ds18b20|ws2812>
P2:<input|dht11|ds18b20|ws2812>
P3:<input|dht11|ds18b20|ws2812>
P4:<input|dht11|ds18b20|ws2812>
P5:<servo180|servo300|servo360>
P6:<servo180|servo300|servo360>

Sending_Interval(0.02-10s): 0.02s
LED_State: on
```

Replace every angle-bracket placeholder before saving this reconstructed template. Choose port values from the actual attached hardware; do not copy the alternatives literally. For DHCP, leave `Static_IP`, `Gateway`, and `Subnet_Mask` blank. For static addressing, all three must be valid IPv4 values, and the gateway must be reachable in the configured subnet.

## Port rules

| Ports | Hardware | Documented configuration values |
| --- | --- | --- |
| P1–P4 | 3-wire I/O | `input`, `dht11`, `ds18b20`, `ws2812` |
| P5–P6 | 5 V servo | `servo180`, `servo300`, `servo360` |
| I2C ×2 | 4-wire I2C | No P-port tag; supported devices are detected automatically |

The Wiki's prose and tables sometimes spell the generic I/O tag as `Input`, while its concrete `config.txt` example uses `input`. Prefer lowercase `input` for generated configuration, preserve a working device file as-is, and flag casing differences for verification rather than silently rewriting them.

`Sending_Interval(0.02-10s)` accepts a documented range of 0.02–10 seconds; the example value includes the `s` suffix. The official `LED_State` setting controls the onboard status indicator and accepts lowercase `on` to enable it or `off` to disable it.

## Observed firmware variants

An actual WIACUBE removable volume may differ from the Wiki reconstruction:

- Shipped files can use `output` on P1–P4. The Wiki does not document this value, but an unchanged factory value should produce a compatibility warning rather than a validation error. For a newly configured unused P1–P4 port, `input` is the documented fallback; changing an existing `output` still requires user confirmation.
- Shipped files can use `State_LED`, but the official field is `LED_State`. Treat `State_LED` as a legacy, non-writable alias: when LED configuration is in scope, replace the key in place with `LED_State` after confirmation. Never retain both aliases. If LED configuration is unrelated to the request, report the validation error and obtain confirmation before normalizing it.
- Extra files written beside `config.txt` may disappear when the virtual FAT volume is remounted. Keep the only backup on a persistent host path, not on the WIAnode volume.

For safer writes, construct and validate a temporary host-side copy first, then copy the validated bytes to the removable volume once. Delete any temporary copy containing credentials after success or failure.

## Verification and recovery

- Press `WKUP` to see the IP address; press it again while the screen is awake to see interface status. The screen sleeps after about one minute without input.
- Yellow breathing: Wi-Fi information has not been configured.
- Red breathing: configuration was saved but Wi-Fi is not connected. Check exact SSID/password, confirm 2.4 GHz support, and power-cycle.
- Green: network connected.
- Before trying firmware replacement, compare the saved file with its backup and validate the network and port values. Firmware updating is outside ordinary config editing.
