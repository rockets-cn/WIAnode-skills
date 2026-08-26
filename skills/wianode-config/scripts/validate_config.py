#!/usr/bin/env python3
"""Read-only validator for a WIAnode config.txt file."""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from pathlib import Path


PORT_VALUES = {
    **{f"P{i}": {"input", "dht11", "ds18b20", "ws2812"} for i in range(1, 5)},
    **{f"P{i}": {"servo180", "servo300", "servo360"} for i in range(5, 7)},
}
FIRMWARE_PORT_VALUES = {
    **{f"P{i}": {"output"} for i in range(1, 5)},
}
KNOWN_KEYS = {
    "WiFi_Name",
    "WiFi_Password",
    "Static_IP",
    "Gateway",
    "Subnet_Mask",
    *PORT_VALUES,
    "Sending_Interval(0.02-10s)",
    "LED_State",
    "State_LED",
}


def read_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    data = Path(source).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("file is not UTF-8/UTF-8-BOM encoded") from exc


def parse(text: str) -> tuple[dict[str, str], list[str], list[str]]:
    values: dict[str, str] = {}
    errors: list[str] = []
    warnings: list[str] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"line {line_no}: expected key:value syntax")
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key in values:
            errors.append(f"line {line_no}: duplicate key {key}")
            continue
        values[key] = value
        if key not in KNOWN_KEYS:
            warnings.append(f"line {line_no}: unknown key {key}; preserved for firmware compatibility")
    return values, errors, warnings


def validate(values: dict[str, str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for key in ("WiFi_Name", "WiFi_Password"):
        if key not in values:
            errors.append(f"missing required key {key}")
        elif not values[key]:
            errors.append(f"{key} is empty")

    static_keys = ("Static_IP", "Gateway", "Subnet_Mask")
    present_static = [key for key in static_keys if values.get(key, "")]
    if present_static and len(present_static) != len(static_keys):
        errors.append("static IPv4 configuration must set Static_IP, Gateway, and Subnet_Mask together")
    elif len(present_static) == len(static_keys):
        try:
            address = ipaddress.IPv4Address(values["Static_IP"])
            gateway = ipaddress.IPv4Address(values["Gateway"])
            network = ipaddress.IPv4Network(
                f'{values["Static_IP"]}/{values["Subnet_Mask"]}', strict=False
            )
            if address in (network.network_address, network.broadcast_address):
                errors.append("Static_IP cannot be the subnet network or broadcast address")
            if gateway not in network:
                errors.append("Gateway is outside the Static_IP subnet")
        except ipaddress.AddressValueError:
            errors.append("Static_IP, Gateway, or Subnet_Mask is not valid IPv4")
        except ipaddress.NetmaskValueError:
            errors.append("Subnet_Mask is not a valid contiguous IPv4 mask")

    for key, allowed in PORT_VALUES.items():
        if key not in values:
            warnings.append(f"missing documented port key {key}")
            continue
        value = values[key]
        if not value:
            warnings.append(f"{key} is empty")
        elif value not in allowed:
            if value.lower() in allowed:
                warnings.append(f"{key} uses non-canonical casing {value}; Wiki examples use {value.lower()}")
            elif value in FIRMWARE_PORT_VALUES.get(key, set()):
                warnings.append(
                    f"{key} uses firmware-specific value {value}; Wiki does not document it"
                )
            else:
                errors.append(f"{key} value is not valid for that port type")

    interval_key = "Sending_Interval(0.02-10s)"
    if interval_key not in values:
        warnings.append(f"missing documented key {interval_key}")
    else:
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)s", values[interval_key])
        if not match:
            errors.append(f"{interval_key} must be a number followed by s")
        elif not 0.02 <= float(match.group(1)) <= 10:
            errors.append(f"{interval_key} must be between 0.02s and 10s")

    has_led_state = "LED_State" in values
    has_legacy_state_led = "State_LED" in values
    if not has_led_state and not has_legacy_state_led:
        warnings.append("missing documented key LED_State")
    else:
        if has_legacy_state_led:
            if has_led_state:
                errors.append("both LED_State and legacy State_LED are present; keep only LED_State")
            else:
                errors.append("legacy key State_LED is not writable; replace it with official LED_State")
        for key in ("LED_State", "State_LED"):
            if key not in values:
                continue
            if values[key] not in {"on", "off"}:
                errors.append(f"{key} must be lowercase on or off")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate WIAnode config.txt without displaying credential values."
    )
    parser.add_argument("config", help="path to config.txt, or - to read stdin")
    args = parser.parse_args()

    try:
        text = read_text(args.config)
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read config: {exc}", file=sys.stderr)
        return 2

    values, parse_errors, parse_warnings = parse(text)
    validation_errors, validation_warnings = validate(values)
    errors = parse_errors + validation_errors
    warnings = parse_warnings + validation_warnings

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    if errors:
        print(f"INVALID: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"VALID: 0 errors, {len(warnings)} warning(s); Wi-Fi password value not displayed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
