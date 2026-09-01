---
name: wianode-touchdesigner
description: Build, inspect, modify, and troubleshoot DFRobot WIAnode interactions in TouchDesigner from natural-language requests through the touchdesigner-mcp tools. Use for mapping WIAnode sensors to visuals, audio, or parameters; creating an MQTT bridge; or safely controlling WIAnode actuators from TouchDesigner. Do not use for unrelated TouchDesigner work or WIAnode config.txt editing.
---

# WIAnode × TouchDesigner

Translate the user's intended interaction into a small, inspectable TouchDesigner network. Use the installed TouchDesigner MCP tools to operate the live project; do not merely describe clicks when those tools are available.

## Route the request

- For MCP installation, connection failure, or tool selection, read [references/touchdesigner-mcp.md](references/touchdesigner-mcp.md). For first-time automatic download, `.tox` import, and Codex MCP registration, also read [references/automatic-install.md](references/automatic-install.md).
- For creating or repairing the WIAnode MQTT connection, decoding sensor packets, or publishing commands, read [references/wianode-bridge.md](references/wianode-bridge.md).
- For mapping sensor values to an effect or preparing an actuator command, read [references/interaction-patterns.md](references/interaction-patterns.md).
- For an existing, partly built project; duplicate MCP components; the post-registration restart gap; save/versioning problems; or a sensor-to-particles-to-servo workflow, read [references/field-tested-workflow.md](references/field-tested-workflow.md).
- WIAnode `config.txt`, Wi-Fi provisioning, and port-mode changes belong to `$wianode-config`. Finish those before building the TouchDesigner interaction when the device is not configured.

## Required context

Collect only values the task actually needs:

- the WIAnode IP shown after pressing `WKUP`;
- each involved port, module name, and printed SKU;
- the desired TouchDesigner target and behavior;
- any input/output range, smoothing, threshold, or fail-safe behavior that cannot be inferred from the existing project.

Treat a generic module name or guessed port as unconfirmed. Sensor-only exploration may continue with an explicit assumption, but never publish an actuator command until its physical port, SKU, configured mode, and safe range are confirmed.

## Live-project workflow

1. Confirm that the TouchDesigner MCP tools are callable. Start with `get_td_info`, then inspect the requested parent network with `get_td_nodes`. If the tools are missing or cannot reach TouchDesigner, run the automatic bootstrap in `references/automatic-install.md` when UI control is available; otherwise provide the exact `.tox` path and remaining manual action. A newly registered MCP server does not appear in the current Codex host until restart; use the bounded loopback bootstrap in `references/field-tested-workflow.md` only when its preconditions hold. Do not claim that the live project was changed until the component or endpoint is verified.
2. Inspect before editing. Look for an existing WIAnode component, MQTT Client DAT, `/project1/wianode_bridge`, and every `/project1/mcp_webserver_base*` component. Prefer the user's existing network and names. Treat a suffixed MCP component as possible collision evidence, not as proof that the original is invalid. Do not replace, delete, or broadly reformat adjacent nodes.
3. Establish the data path. Reuse the official WIAnode component when present. Otherwise create a dedicated `wianode_bridge` Base COMP with an MQTT Client DAT, callbacks DAT, and sensor-value table as described in `references/wianode-bridge.md`.
4. Verify the connection before building downstream logic: check the MQTT DAT's `isConnected`, subscribe to `topic_input`, observe at least one valid JSON object when live sensor data is available, and report the actual keys discovered.
5. Build the requested interaction as the smallest reversible slice. Prefer normal TouchDesigner nodes and parameters for visible dataflow. Use `execute_python_script` only for operations not expressible through node creation, parameter updates, or node methods; keep scripts bounded and return a compact `result` object.
6. Preserve existing behavior. Put new nodes under the agreed parent, use descriptive names, avoid deleting unknown nodes, and change only parameters that implement the request.
7. Verify after the final edit with `get_td_node_errors`. For visual output, inspect the relevant TOP with `get_top_image`. Exercise meaningful endpoints for count/range mappings, re-read changed parameters, and save only after the target path and overwrite behavior are known. When physical observation is unavailable, label it `待用户确认`.

## Hardware-output confirmation gate

TouchDesigner network edits requested by the user are reversible and may proceed. Publishing to `topic_output` can move hardware or drive lights, so it requires a separate confirmation immediately before the first real publish.

Show this preview without exposing credentials:

- WIAnode IP and MQTT topic;
- exact JSON payload;
- physical port, module, SKU, and configured mode;
- allowed range and the clamped value to be sent;
- expected physical effect and how to stop it.

Ask `确认发送上述 WIAnode 控制指令吗？` Publish only after an affirmative reply to that preview. Send one bounded command, do not set MQTT retain unless explicitly requested, then report the broker result separately from the unobservable physical result. If the request is for continuous control, keep it disarmed until the user confirms the physical response and explicitly authorizes the continuous mapping, including its range, dead zone/rate limit, and stop method. A prior request to build the network is not authorization to actuate hardware.

## Completion report

Report:

- TouchDesigner project path and nodes created or changed;
- WIAnode IP, confirmed port/SKU, subscribed sensor keys, and mappings;
- MQTT and node-error verification results;
- actuator commands actually sent, if any;
- whether continuous output is armed and the exact way to stop it;
- visual or physical checks that remain `待用户确认`.

Never expose Wi-Fi or MQTT passwords in summaries, screenshots, node labels, or returned script results.
