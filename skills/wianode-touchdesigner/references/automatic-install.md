# Automatic TouchDesigner MCP installation

Read this reference only when TouchDesigner MCP or `mcp_webserver_base.tox` is missing. It covers the automation bootstrap before MCP tools are available. The release layout and CLI command follow [touchdesigner-mcp's installation guide](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md), checked at `v2.0.0` on 2026-09-01. This third-party automation component is separate from DFRobot's `WIAnode_plugin_10828.tox`; prepare and import the latter through [official-wianode-plugin.md](official-wianode-plugin.md).

## Authorization boundary

- If the user explicitly asks to install, configure, or automatically import TouchDesigner MCP, proceed through bundled-component import and new MCP registration without a second confirmation.
- If installation is only discovered as a prerequisite, preview the bundled component path and upstream source, target project path, intended `/project1/mcp_webserver_base` node, and `touchdesigner` MCP entry; obtain one confirmation before mutation.
- Import only into the currently selected TouchDesigner project. If several projects or processes are open and the target is unclear, ask which project.
- If `/project1/mcp_webserver_base` or a `touchdesigner` MCP entry already exists, inspect it. Reuse a matching installation. Do not replace or remove a conflicting installation without showing the difference and obtaining confirmation.
- Stop for unexpected EULA, login, license, security-permission, or overwrite prompts instead of accepting them silently.

## 1. Use the bundled MCP component

The complete upstream bundle is stored in the installed skill at:

```text
assets/touchdesigner-mcp-td/
├── mcp_webserver_base.tox
├── import_modules.py
└── modules/
```

Use the bundled `.tox` for ordinary installation and resolve it to an absolute path. Do not move it away from `import_modules.py` and `modules/`; the component imports them by relative path. Provenance and checksums are recorded in `assets/SOURCES.json`.

Run the helper only to refresh the bundle from the touchdesigner-mcp latest release. Use `python3` on macOS/Linux:

```text
python3 scripts/prepare_touchdesigner_mcp.py
```

On Windows use the Python launcher:

```text
py -3 scripts/prepare_touchdesigner_mcp.py
```

The helper downloads only the touchdesigner-mcp project's latest-release archive, rejects path traversal and symbolic links, limits extracted size, verifies that `mcp_webserver_base.tox`, `import_modules.py`, and `modules/` are present, and extracts the complete bundle under `~/.codex/tools/touchdesigner-mcp/<sha-prefix>/`. A repeated run with the same archive reuses the checksum-addressed directory.

## 2. Import `.tox` with Computer Use

The import cannot use TouchDesigner MCP because its WebServer component is not running yet. Use the available Computer Use capability to operate TouchDesigner directly:

1. Inspect the current TouchDesigner application state. Launch TouchDesigner only when no instance is running.
2. Confirm the intended project is open and navigate the active Network Editor to `/project1`. Do not create a new project when the user has an existing target project.
3. Inspect the network for `mcp_webserver_base`. Also probe `http://127.0.0.1:9981/api/td/server/td` before importing: a healthy component may be off-screen even when it is not visible in the current Network Editor. If a matching component or verified endpoint already exists, inspect and reuse it instead of importing.
4. Open `File → Import File…`. In the native file picker, enter the absolute bundled `assets/touchdesigner-mcp-td/mcp_webserver_base.tox` path and choose the file. If a refresh was explicitly performed, use the helper's `tox_path` instead. Prefer the file dialog over double-clicking the `.tox`; double-clicking starts a separate TouchDesigner process instead of importing into the current network.
5. After every UI action, fetch fresh application state before choosing the next control. Do not reuse stale accessibility element indexes.
6. If an overwrite/name-collision dialog appears, cancel and inspect the existing component. TouchDesigner can also silently suffix the import without a dialog, so do not assume the absence of a prompt means there was no collision.
7. Re-enumerate every `/project1/mcp_webserver_base*` component after import. Compare port, source `.tox`, and errors. If the original is healthy and the suffixed component was created by this operation, remove only that new duplicate; otherwise stop and report the conflict.
8. Verify that the retained `/project1/mcp_webserver_base` is visible or reachable. Open Textport (`Alt+T` or `Dialogs → Textport`) only if the component does not appear healthy or the HTTP check below fails.

If Computer Use is unavailable or the TouchDesigner Network Editor is inaccessible, give the user the exact bundled `.tox` path and ask them to drag that file into `/project1`. Record the import as incomplete; do not continue with live MCP claims.

## 3. Verify the TouchDesigner WebServer

After import, check the local API without exposing it beyond loopback:

```text
curl --fail --silent --show-error http://127.0.0.1:9981/api/td/server/td
```

Require a successful JSON response. If port `9981` is already occupied or the component reports an error, inspect the component and Textport; do not change firewall or network-security settings as an automatic repair.

This verifies only the automation layer. It does not verify that `WIAnode_plugin_10828.tox` is present or that WIAnode data is connected.

## 4. Register the Codex MCP server

Inspect before mutating:

```text
codex mcp get touchdesigner --json
```

If no entry exists, add the official npm stdio server:

```text
codex mcp add touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

If an existing entry matches, keep it. If it differs, show the current and proposed command and ask before replacing it. Never remove an existing entry merely because the add command failed.

Codex stores MCP configuration in `~/.codex/config.toml` by default. The user must restart the Codex host after a new entry is added. After restart, resume with `get_td_info`, `get_td_nodes` on `/project1`, and `get_td_node_errors` on `/project1/mcp_webserver_base`. Report these separately:

- bundled component path and layout verified;
- `.tox` imported into the intended project;
- HTTP API reachable on loopback;
- Codex MCP entry added or reused;
- post-restart MCP tools verified or still pending restart.

The current host does not dynamically gain newly registered MCP tools. If the user already authorized live edits and the verified loopback endpoint is needed to finish an in-progress repair before restart, follow the bounded restart-gap bridge in [field-tested-workflow.md](field-tested-workflow.md); do not present it as a substitute for the restart.
