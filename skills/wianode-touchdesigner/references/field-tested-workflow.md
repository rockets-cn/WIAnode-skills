# Field-tested TouchDesigner workflow

Read this reference when repairing an existing project, bootstrapping immediately after MCP registration, handling duplicate WebServer components or save prompts, or building an exact particle-count-to-servo interaction. These observations were validated on Windows with TouchDesigner `2025.33070`, touchdesigner-mcp `v2.0.0`, and a real WIAnode on 2026-09-01. Re-check version-sensitive details elsewhere.

## What was verified

- The official component bundle was prepared, imported, and reachable at `http://127.0.0.1:9981`.
- The Codex stdio entry was registered successfully; the current Codex host still required restart before MCP tools appeared.
- An existing `/project1` network was inspected and repaired through the verified loopback API during that restart gap.
- A normalized P1 rotary value drove an exact `0..300` particle count.
- Particle count drove a confirmed P5 `SER0053` in `servo300` mode over a user-confirmed mechanical range of `30..270` degrees.
- A single `{"p5":"150"}` test physically moved the servo; continuous output was armed only after the user confirmed that movement.

## Bootstrap without creating a duplicate

Before importing, test the loopback server even when the node is not visible in the current Network Editor. A successful `/api/td/server/td` response can reveal a healthy off-screen component.

TouchDesigner may silently import a second component as `mcp_webserver_base1` without showing a collision dialog. After import, enumerate every `/project1/mcp_webserver_base*` node and compare port, source `.tox`, and errors. If the original is healthy and the suffixed node was created by the current operation, remove only that new duplicate. Otherwise stop and show the conflict.

## Bounded loopback restart-gap bridge

After `codex mcp add`, restart remains the supported way to expose MCP tools. When the user already authorized live-project edits, the loopback WebServer has been verified, and restarting would interrupt the current repair, a temporary bounded call may use:

```text
POST http://127.0.0.1:9981/api/td/server/exec
Content-Type: application/json

{"script":"result = {'ok': True}"}
```

Keep each script small, inspect before mutation, and return compact evidence. In the validated server, nested dictionaries assigned as values inside `result` could be coerced into unrelated operator descriptions. Prefer a top-level result object whose structured collections are lists of small record dictionaries.

This bridge is not a replacement for restarting Codex and using the MCP tools on later turns.

## Exact particle count

A Particle SOP `birth` expression is not an exact count controller: birth rate, lifetime, frame rate, and internal limits can make most of the sensor range saturate at the same population. For a requested quantity, use an explicit population stage:

```text
sensor_values[p1_input_val]
→ Constant CHOP expression
→ Filter CHOP + clamp 0..1
→ Script POP creates round(value * 300) points
→ Copy POP copies the visible particle to those points
```

Keep point positions deterministic when only the population should change. Verify `0 → 0`, `0.1 → 30`, `0.9 → 270`, and `1 → 300`, then inspect low/high TOP images and node errors.

## Actuator arming sequence

Use two independent interlocks for continuous physical output when an external bridge is involved:

1. Keep the bridge's hardware-output flag off and automatic sensor-follow disabled.
2. Keep the TouchDesigner CHOP Execute DAT inactive and its stored `confirmed` / `output_enabled` flags false.
3. Build and verify only the preview mapping.
4. Preview one exact payload and obtain confirmation.
5. Send one bounded command with QoS 0 and retain false.
6. Confirm broker acceptance separately from physical motion.
7. Arm continuous output only after the user confirms the physical response and the continuous range, dead zone/rate limit, and stop method.

For the validated P5 `SER0053` balance-scale interaction, particles `0..300` mapped to `30..270` degrees with a `3°` dead zone and a minimum `0.12 s` publish interval. These are a field-tested example, not defaults for another servo or mechanism.

If a publish request loses its HTTP response after the command may have been sent, treat the outcome as uncertain and do not retry blindly. Inspect the bridge and ask about physical movement. In the validated run, the connection closed before the client received a response, while the user observed the servo move.

## Saving without blocking the API

TouchDesigner `2025.33070` exposes `project.save(...)`, not `project.saveAs(...)`. Saving can create versioned siblings such as `.1.toe`, `.2.toe`, and a canonical `.toe`; an existing target may open a modal and stall the loopback request.

Preflight the target path. Prefer a new destination or use Computer Use for an expected overwrite prompt. After saving, re-read `project.folder`, `project.name`, the filesystem path, file size, and timestamp. If an API call times out after save, inspect the TouchDesigner window for a modal before retrying.
