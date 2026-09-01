# Official WIAnode TouchDesigner plugin

Read this reference before importing, locating, or using WIAnode-facing nodes. The only plugin authority for this skill is [DFRobot/WIAnode-examples](https://github.com/DFRobot/WIAnode-examples), checked at commit `688c851a5dc3f976ed113e40ea3602e8abd701d7` on 2026-09-01.

## Required files

The repository publishes:

- `WIAnode-Touchdesigner-plugin/WIAnode_plugin_10828.tox` — the DFRobot WIAnode component;
- `WIAnode-Touchdesigner-plugin/WIAnode_plugin_10828_sample.toe` — the component sample project;
- `WIAnode_Touchdesigner_samples/` — device-specific `.toe` examples.

The skill includes a verified copy at:

```text
assets/dfrobot-wianode/WIAnode_plugin_10828.tox
```

Use the bundled file for ordinary imports. Its provenance and SHA-256 are recorded in `assets/SOURCES.json`.

Run the helper only when refreshing from DFRobot or when the official sample project and device-specific examples are needed:

```text
python3 scripts/prepare_wianode_td_plugin.py
```

On Windows:

```text
py -3 scripts/prepare_wianode_td_plugin.py
```

The JSON result contains `plugin_path`, `plugin_sample_path`, `examples_dir`, repository URL, archive checksum, and the locally extracted files. Use the bundled or freshly validated official path; do not substitute a similarly named `.tox` from another repository.

## Import without replacing the user's project

Import the bundled `assets/dfrobot-wianode/WIAnode_plugin_10828.tox` into the intended TouchDesigner project with `File → Import File…` or drag-and-drop. Resolve it to an absolute path from the installed skill directory. Before importing:

1. Inspect `/project1` with `get_td_nodes` for a component whose actual path, parameters, or external `.tox` source identifies the DFRobot plugin.
2. Reuse a matching component. Do not assume the operator name after import; TouchDesigner may normalize or suffix it.
3. If import is required, use Computer Use when available. If the installed MCP exposes and documents a suitable import method through `get_td_class_details` or `get_td_module_help`, that verified method may be used instead.
4. Re-enumerate `/project1`, identify the new component by before/after comparison, inspect its parameters, and check its errors.

Opening a `.toe` replaces the active project. Inspect an official example in a separate TouchDesigner instance/project, or obtain user authorization before switching away from an unsaved current project.

## Official example routing

Use the closest matching example as the source for WIAnode-facing behavior:

| Interaction | Official example |
| --- | --- |
| Button | `01.WIAnode-TD-button/wianode-button.toe` |
| Knob | `02.WIAnode-TD-knob/wianode-knob.toe` |
| Microphone | `03.WIAnode-TD-microphone/wianode-microphone.toe` |
| Light | `04.WIAnode-TD-light/wianode-light.toe` |
| Ultrasonic distance | `05.WIAnode-TD-ultrasonic/wianode-distance.toe` |
| Millimeter-wave sensor | `06.WIAnode-TD-mmwave/wianode-mmwave.toe` |
| Accelerometer | `07.WIAnode-TD-accelerometer/wianode-accelerometer.toe` |
| Gesture | `08.WIAnode-TD-gesture/wianode-gesture.toe` |
| LED | `09.WIAnode-TD-LED/wianode-led.toe` |
| 300° servo | `10.WIAnode-TD-servo300/wianode-servo300.toe` |
| IO touch | `11.WIAnode-TD-IO-TD-touch/WIAnode-IO-touch.toe` |
| Hall sensor | `12.WIAnode-TD-IO-TD-hall/WIAnode-hall.toe` |
| Temperature and humidity | `13.WIAnode-TD-IO-TD-tem&humi/WIAnode-tem&humi.toe` |
| I2C color | `14.WiaNode-TD-I2C-TD-color/WiaNode-I2C-color.toe` |
| Environmental sensor | `15.WiaNode-TD-IO-TD-envionment/WiaNode-envionment.toe` |

The upstream `readme` is empty and `.tox`/`.toe` files are binary. Therefore the table proves example availability, not internal parameter names or protocol details. Use touchdesigner-mcp to inspect the loaded official component/example and copy the observed data path. Do not guess undocumented names, ranges, topics, payloads, or callback code.

## Strict fallback rule

If the bundled official plugin is missing, fails its recorded checksum, or cannot be imported or inspected:

- report the exact missing file or failed inspection;
- provide the validated official file path when only manual import remains;
- do not create a replacement MQTT Client DAT, callback DAT, external bridge, or protocol implementation;
- do not claim that WIAnode data is connected.

Custom TouchDesigner visuals remain allowed after an official-plugin output is observed. Keep those downstream nodes separate and label them as project-specific.
