# Automatic TouchDesigner MCP installation

Read this reference only when TouchDesigner MCP or `mcp_webserver_base.tox` is missing. It covers the bootstrap phase before TouchDesigner MCP tools are available. The release layout and CLI command follow [touchdesigner-mcp's installation guide](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md), reviewed at `v2.0.0` on 2026-08-25. TouchDesigner officially supports importing `.tox` files through `File → Import File…` or drag-and-drop.

## Authorization boundary

- If the user explicitly asks to install, configure, or automatically import TouchDesigner MCP, proceed through the download, import, and new MCP registration without a second confirmation.
- If installation is only discovered as a prerequisite, preview the official download source, target project path, intended `/project1/mcp_webserver_base` node, and `touchdesigner` MCP entry; obtain one confirmation before mutation.
- Import only into the currently selected TouchDesigner project. If several projects or processes are open and the target is unclear, ask which project.
- If `/project1/mcp_webserver_base` or a `touchdesigner` MCP entry already exists, inspect it. Reuse a matching installation. Do not replace or remove a conflicting installation without showing the difference and obtaining confirmation.
- Stop for unexpected EULA, login, license, security-permission, or overwrite prompts instead of accepting them silently.

## 1. Prepare the official component bundle

Run the helper from the installed skill directory. Use `python3` on macOS/Linux:

```text
python3 scripts/prepare_touchdesigner_mcp.py
```

On Windows use the Python launcher:

```text
py -3 scripts/prepare_touchdesigner_mcp.py
```

The helper downloads only the official latest-release archive, rejects path traversal and symbolic links, limits extracted size, verifies that `mcp_webserver_base.tox`, `import_modules.py`, and `modules/` are present, and extracts the complete bundle under `~/.codex/tools/touchdesigner-mcp/<sha-prefix>/`. Parse its JSON output and retain `tox_path` and `bundle_dir`.

Do not move the `.tox` away from `import_modules.py` and `modules/`; the component imports them by relative path. A repeated run with the same archive reuses the checksum-addressed directory.

## 2. Import `.tox` with Computer Use

The import cannot use TouchDesigner MCP because its WebServer component is not running yet. Use the available Computer Use capability to operate TouchDesigner directly:

1. Inspect the current TouchDesigner application state. Launch TouchDesigner only when no instance is running.
2. Confirm the intended project is open and navigate the active Network Editor to `/project1`. Do not create a new project when the user has an existing target project.
3. Inspect the network for `mcp_webserver_base`. If a matching component already exists, skip import.
4. Open `File → Import File…`. In the native file picker, enter the absolute `tox_path` from the helper output and choose the file. Prefer the file dialog over double-clicking the `.tox`; double-clicking starts a separate TouchDesigner process instead of importing into the current network.
5. After every UI action, fetch fresh application state before choosing the next control. Do not reuse stale accessibility element indexes.
6. If an overwrite/name-collision dialog appears, cancel and inspect the existing component. Do not create `mcp_webserver_base1` as an unnoticed duplicate.
7. Verify that `/project1/mcp_webserver_base` is visible in the current Network Editor. Open Textport (`Alt+T` or `Dialogs → Textport`) only if the node does not appear healthy or the HTTP check below fails.

If Computer Use is unavailable or the TouchDesigner Network Editor is inaccessible, give the user the exact `tox_path` and ask them to drag that file into `/project1`. Record the import as incomplete; do not continue with live MCP claims.

## 3. Verify the TouchDesigner WebServer

After import, check the local API without exposing it beyond loopback:

```text
curl --fail --silent --show-error http://127.0.0.1:9981/api/td/server/td
```

Require a successful JSON response. If port `9981` is already occupied or the component reports an error, inspect the component and Textport; do not change firewall or network-security settings as an automatic repair.

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

- component downloaded and layout verified;
- `.tox` imported into the intended project;
- HTTP API reachable on loopback;
- Codex MCP entry added or reused;
- post-restart MCP tools verified or still pending restart.
