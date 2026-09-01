---
name: wianode-touchdesigner
description: Build, inspect, modify, and troubleshoot DFRobot WIAnode interactions in TouchDesigner. Use the DFRobot WIAnode plugin and examples for device-facing behavior, and use touchdesigner-mcp only to inspect and operate the live TouchDesigner project. Do not use for unrelated TouchDesigner work or WIAnode config.txt editing.
---

# WIAnode × TouchDesigner

Translate the user's intended interaction into a small, inspectable TouchDesigner network. Keep these two components separate:

- **WIAnode device layer:** use the bundled `assets/dfrobot-wianode/WIAnode_plugin_10828.tox`, sourced from [DFRobot/WIAnode-examples](https://github.com/DFRobot/WIAnode-examples). The matching upstream examples remain the authority for WIAnode-facing behavior.
- **Automation layer:** use the complete bundled `assets/touchdesigner-mcp-td/` package from [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) to inspect and operate TouchDesigner. Its `mcp_webserver_base.tox` does not replace or define the WIAnode plugin.

## Route the request

- Before importing, locating, or using WIAnode components or examples, read [references/official-wianode-plugin.md](references/official-wianode-plugin.md).
- For MCP installation, connection failure, or tool selection, read [references/touchdesigner-mcp.md](references/touchdesigner-mcp.md). For first-time automatic preparation, `.tox` import, and Codex MCP registration, also read [references/automatic-install.md](references/automatic-install.md).
- For mapping a verified official-plugin output to a visual or actuator workflow, read [references/interaction-patterns.md](references/interaction-patterns.md).
- For an existing, partly built project; duplicate MCP components; the post-registration restart gap; save/versioning problems; or a sensor-to-particles workflow, read [references/field-tested-workflow.md](references/field-tested-workflow.md).
- WIAnode `config.txt`, Wi-Fi provisioning, and port-mode changes belong to `$wianode-config`.

## Source boundary

Do not recreate the WIAnode connection with a custom MQTT Client DAT, callback script, external bridge, guessed topic, or guessed payload. Do not infer official plugin parameters or data keys from module names. If the DFRobot plugin or relevant example cannot be obtained or inspected, stop the WIAnode-facing part and report the missing evidence.

Custom CHOP/POP/TOP processing is allowed only downstream of a value actually exposed by the official plugin or official example. Label those downstream networks as project-specific, not DFRobot behavior.

## Live-project workflow

1. Confirm the automation layer. Start with `get_td_info`, then `describe_td_tools` when the installed schemas are unfamiliar, and inspect `/project1` with `get_td_nodes`. If the MCP tools are unavailable, import the bundled `assets/touchdesigner-mcp-td/mcp_webserver_base.tox` with its directory intact and follow `references/automatic-install.md`. A newly registered MCP server normally requires a Codex restart.
2. Confirm the device layer. Locate the imported DFRobot WIAnode component and inspect its actual path and parameters. If absent, import the bundled `assets/dfrobot-wianode/WIAnode_plugin_10828.tox` as described in `references/official-wianode-plugin.md`. Do not substitute `mcp_webserver_base.tox` for it.
3. Use the closest official `.toe` example as the behavioral reference. Inspect it in a separate project or instance when opening it would replace the user's current project. Copy only the relevant verified pattern into the target project.
4. Inspect before editing. Use `get_td_nodes` and `get_td_node_parameters`; use `get_td_classes`, `get_td_class_details`, or `get_td_module_help` instead of guessing unfamiliar TouchDesigner APIs. Preserve adjacent nodes and existing names.
5. Build the smallest reversible downstream slice with `create_td_node`, `update_td_node_parameters`, and `exec_node_method`. Use `execute_python_script` only when the operation is not available through the narrower tools, and keep the script bounded and inspectable.
6. Delete only nodes created by the current operation and only when rollback or cleanup requires it. Never delete or replace an existing official WIAnode component, official-example network, or MCP component without identifying it and obtaining authorization when replacement is necessary.
7. Verify with re-read parameters and `get_td_node_errors`. For visual output, capture the relevant TOP with `get_top_image`. Report the official component/example used and distinguish verified TouchDesigner state from physical behavior that remains `待用户确认`.

## Hardware-output confirmation gate

TouchDesigner network edits requested by the user are reversible and may proceed. A real actuator action still requires a separate confirmation immediately before the first output.

Derive the command path and value format from the imported DFRobot plugin or the matching official example. Show, without credentials:

- official example or inspected official-plugin node used as evidence;
- physical port, module, SKU, and configured mode;
- exact official-plugin parameter/value or command that will be applied;
- allowed range, clamped value, expected effect, and stop method.

Ask `确认执行上述 WIAnode 控制操作吗？` Perform one bounded operation only after an affirmative reply. Report TouchDesigner/plugin acceptance separately from physical motion. Continuous control requires another explicit authorization after the user confirms the single physical test, including its range, dead zone/rate limit, and stop method.

## Completion report

Report:

- TouchDesigner project path and nodes created or changed;
- DFRobot plugin path/source and official example used;
- WIAnode port/SKU and actual plugin outputs or parameters observed;
- MCP connection, parameter re-read, node-error, and image verification results;
- actuator operations actually performed and whether continuous output is armed;
- visual or physical checks that remain `待用户确认`.

Never expose Wi-Fi or MQTT passwords in summaries, screenshots, node labels, or returned script results.
