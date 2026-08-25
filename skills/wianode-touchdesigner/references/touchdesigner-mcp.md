# TouchDesigner MCP setup and tool routing

Read this reference when TouchDesigner tools are missing, the MCP bridge cannot connect, or a live-project operation needs the correct tool. Source: [8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp), reviewed at release `v2.0.0` on 2026-08-25.

## Required setup

1. Use TouchDesigner and Node.js 20 or newer.
2. Download `touchdesigner-mcp-td.zip` from the project's [latest release](https://github.com/8beeeaaat/touchdesigner-mcp/releases/latest), keep its extracted folder layout intact, and import `mcp_webserver_base.tox` into the TouchDesigner project. `/project1/mcp_webserver_base` is the recommended path. Use [automatic-install.md](automatic-install.md) to perform these steps automatically when computer-use capability is available.
3. Add the stdio server to Codex:

   ```text
   codex mcp add touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
   ```

4. Restart Codex after changing MCP configuration. Keep TouchDesigner open and the imported WebServer component running. The default TouchDesigner endpoint is `http://127.0.0.1:9981`.

An explicit request to install or configure TouchDesigner MCP authorizes downloading the official release, importing the component into the currently selected project, and adding a new `touchdesigner` MCP entry. If installation is only an inferred prerequisite to another request, show one concise installation preview and obtain approval before changing Codex configuration or the TouchDesigner project. Never silently replace an existing MCP entry or an existing `mcp_webserver_base` component with different contents.

## Tool choice

| Intent | Tool |
| --- | --- |
| Verify TouchDesigner connection/build | `get_td_info` |
| List or find nodes | `get_td_nodes` |
| Inspect exact parameter names and values | `get_td_node_parameters` |
| Create one node | `create_td_node` |
| Change known parameters | `update_td_node_parameters` |
| Connect nodes or call an OP method | `exec_node_method` or `execute_python_script` |
| Run bounded TouchDesigner Python | `execute_python_script` |
| Diagnose a node tree | `get_td_node_errors` |
| Inspect visual output | `get_top_image` |
| Discover unfamiliar TD classes/APIs | `get_td_classes`, `get_td_class_details`, `get_td_module_help` |
| Discover the installed tool schema | `describe_td_tools` |

Use read tools before mutation tools. Query actual node parameters instead of guessing parameter names across TouchDesigner versions. Prefer several small operations over one opaque project-wide script.

## Connection diagnosis

- `ECONNREFUSED`: start TouchDesigner, ensure the imported WebServer DAT is active, and verify port `9981`.
- Timeout: inspect the WebServer DAT, firewall, and host configuration; then retry once after the condition changes.
- Host lookup error: use `127.0.0.1` unless the WebServer is intentionally remote.
- API compatibility error: update both the npm MCP server and the `.tox` component from the same current release. The project documents API compatibility separately from the npm package version.
- The MCP client caches a failed TouchDesigner connection briefly. After fixing the underlying issue, wait for the retry window or restart the MCP client instead of repeatedly issuing mutations.

## Evidence before completion

A successful MCP response proves only that TouchDesigner accepted the operation. Verify the requested outcome with node parameters, `get_td_node_errors`, and—when relevant—`get_top_image`. It does not prove that a physical WIAnode actuator moved.
