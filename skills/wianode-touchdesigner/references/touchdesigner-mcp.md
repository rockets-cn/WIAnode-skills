# TouchDesigner MCP automation layer

Read this reference when TouchDesigner tools are missing, the MCP bridge cannot connect, or a live-project operation needs the correct tool. Source: [8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp), checked at commit `a6908cd2f089fa49ab1df1fa34a0802fc9647cea` (`v2.0.0`) on 2026-09-01.

## Responsibility boundary

TouchDesigner MCP bridges an AI agent to TouchDesigner's WebServer DAT. It can inspect project structure, create/update/delete nodes, call node methods, execute Python, discover TouchDesigner classes, inspect errors, and capture TOP images.

It is not the DFRobot WIAnode plugin. Keep `mcp_webserver_base.tox` for automation and `WIAnode_plugin_10828.tox` for WIAnode device behavior. Never use MCP's general Python or node tools to invent a replacement WIAnode protocol implementation.

## Required setup

1. Use TouchDesigner and Node.js 20 or newer.
2. Use the complete bundle stored at `assets/touchdesigner-mcp-td/`. Keep `mcp_webserver_base.tox`, `import_modules.py`, and `modules/` together, and import the `.tox` into the TouchDesigner project. `/project1/mcp_webserver_base` is recommended. Use the upstream [latest release](https://github.com/8beeeaaat/touchdesigner-mcp/releases/latest) only when intentionally refreshing the bundled copy.
3. Add the stdio server to Codex:

   ```text
   codex mcp add touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
   ```

4. Restart Codex after changing MCP configuration. Keep TouchDesigner and the imported WebServer component running. The default TouchDesigner endpoint is `http://127.0.0.1:9981`.

Use [automatic-install.md](automatic-install.md) for the guarded bundled-component import and registration workflow. Provenance and checksums are recorded in `assets/SOURCES.json`. Do not call this third-party automation component a DFRobot or WIAnode plugin.

## Tool routing

The installed server is authoritative for its current schemas. Call `describe_td_tools` when signatures are unclear and do not rely on remembered arguments across versions.

| Intent | Tool | Decision rule |
| --- | --- | --- |
| Verify server/build | `get_td_info` | First live call |
| Discover current tool manifest | `describe_td_tools` | Use when schemas or available tools are uncertain |
| List/filter nodes | `get_td_nodes` | Inspect before mutation; use bounded detail/limits |
| Read exact parameters | `get_td_node_parameters` | Required before changing version-sensitive or custom parameters |
| Create a node | `create_td_node` | Only for downstream project logic, not a replacement WIAnode bridge |
| Update parameters | `update_td_node_parameters` | Re-read the result; retry only failed parameters |
| Call a node method | `exec_node_method` | Use when the method is already known or discovered |
| Delete a node | `delete_td_node` | Only for a node created by the current operation or an explicitly approved target |
| Execute TouchDesigner Python | `execute_python_script` | Last resort for bounded operations not covered above |
| Check node/descendant errors | `get_td_node_errors` | Required after final edits |
| Capture a TOP | `get_top_image` | Visual evidence; optional `maxSize` preserves aspect ratio |
| List Python classes/modules | `get_td_classes` | Discover unfamiliar APIs |
| Inspect class members | `get_td_class_details` | Confirm methods/properties before calling them |
| Read Python `help()` | `get_td_module_help` | Resolve an unfamiliar TouchDesigner module/class |

`get_top_image` uses the Python execution channel internally and returns a JPEG. When it downscales, upstream creates and destroys a temporary Resolution TOP, leaving the project unchanged.

Prefer the narrow tool that expresses the operation. Keep `execute_python_script` small, return a compact `result`, and never include credentials or broad project dumps. For unfamiliar official WIAnode components, inspect their real paths and parameters; do not infer them from the binary filename.

## Version compatibility

The npm package version and TouchDesigner component API version are separate. `v2.0.0` expects API `1.5.0` and supports API `1.3.0` or newer within the documented compatibility rules. A warning may still allow operations; an incompatibility error requires updating both sides from the same touchdesigner-mcp release. Updating this automation layer must not replace the DFRobot WIAnode plugin.

## Current-host restart gap

Registering the stdio entry does not add new tools to an already-running Codex host. Restart remains the supported path. When the loopback WebServer is verified and an already-authorized repair must finish before restart, the bounded `/api/td/server/exec` bridge in [field-tested-workflow.md](field-tested-workflow.md) may be used temporarily.

## Connection diagnosis

- `ECONNREFUSED`: start TouchDesigner and verify the MCP WebServer component and port `9981`.
- Timeout: inspect the WebServer DAT, firewall, and TouchDesigner UI for blocking dialogs before retrying.
- Host lookup error: use `127.0.0.1` unless a different host was intentionally configured.
- Compatibility error: update the npm server and `mcp_webserver_base.tox` bundle together.
- A failed TouchDesigner connection is cached briefly. Fix the condition before retrying instead of issuing repeated mutations.

## Evidence before completion

An MCP success means TouchDesigner accepted the operation. Re-read changed parameters, run `get_td_node_errors`, and use `get_top_image` for visual work. It does not prove that the DFRobot plugin connected to hardware or that an actuator moved; report those separately.
