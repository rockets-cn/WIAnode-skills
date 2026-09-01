# WIAnode interaction patterns

Read this reference when mapping an output from the imported DFRobot WIAnode plugin to downstream TouchDesigner nodes. Read [official-wianode-plugin.md](official-wianode-plugin.md) first and choose the matching official `.toe` example.

## Evidence chain

Resolve this chain before editing:

```text
confirmed physical module and port
→ matching DFRobot example
→ observed official-plugin node/path/parameter or channel
→ project-specific normalization/filter
→ TouchDesigner target
→ visible verification
```

Use `get_td_nodes` and `get_td_node_parameters` to record the actual official-plugin output. Do not guess a channel, MQTT key, topic, payload, callback, or parameter from the module name. The DFRobot repository's `.tox` and `.toe` files are binary and its plugin `readme` is empty, so filenames alone are not an API specification.

## Downstream visual mappings

Once an official-plugin value is observed, custom CHOP/POP/TOP processing may be added downstream. Keep the DFRobot component intact and place project-specific nodes under a clearly named Base COMP or alongside the user's existing visual network.

- Reuse an existing Select/Math/Filter/Logic chain when it already expresses the requested mapping.
- State and clamp the observed source range and requested destination range.
- Change the normalization or filter stage for requests such as “更灵敏”, “平滑一点”, or “反过来”.
- Re-read the target parameters and capture the final TOP after edits.

These nodes are custom project logic, not DFRobot plugin behavior.

## Exact quantity controls

When the user asks for an exact particle or instance count, do not treat a Particle SOP birth rate as the current population. A project-specific explicit population stage may create `round(clamp(value, 0, 1) * max_count)` points and feed a Copy POP. Keep positions deterministic when only population should change, then verify both endpoints and at least two interior values.

This technique is a downstream TouchDesigner pattern. It does not define how the WIAnode plugin exposes a knob or sensor; obtain that input from the loaded official component/example first.

## Official example selection

Use the example table in [official-wianode-plugin.md](official-wianode-plugin.md). Examples currently cover button, knob, microphone, light, ultrasonic distance, millimeter-wave, accelerometer, gesture, LED, 300° servo, IO touch, Hall, temperature/humidity, I2C color, and environmental sensing.

If no official example matches, inspect `WIAnode_plugin_10828_sample.toe` and the imported official component. If the required WIAnode-facing behavior remains unverified, stop rather than inventing it. A custom visual may still be demonstrated with clearly labeled simulated input only when the user explicitly requests simulation.

## Actuator mappings

Derive the output node, parameter/value format, and update mechanism from the matching official example. Do not bypass the official plugin with a custom MQTT publisher.

1. Build a preview-only downstream mapping and keep its final actuator-driving path inactive.
2. Confirm the physical port, SKU, configured mode, mechanical range, rate limit/dead zone, and stop method.
3. Show the exact inspected official-plugin parameter/value or operation and obtain confirmation.
4. Apply one bounded test through the official-plugin path.
5. Report plugin acceptance separately from physical motion.
6. Arm continuous output only after the user confirms the physical test and separately authorizes continuous control.

If the operation loses its response after it may have executed, do not retry blindly; inspect current TouchDesigner state and ask whether the actuator moved.

## Verification

After mapping sensor input, report the observed official-plugin source path/value and mapped output value. After a visual edit, run `get_td_node_errors` and `get_top_image`. After a hardware operation, report only the TouchDesigner/plugin result unless physical behavior is confirmed by the user.
