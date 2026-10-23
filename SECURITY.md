# Security and execution boundaries

Use the public `ip-forge mcp` entry point. It exposes inspection/report tools by
default; execution requires `--allow-execution`. Legacy API/server routes are not
part of the supported alpha. Do not expose this local stdio server over a public port.

Flutter execution is not sandboxed and runs with the current user's privileges.
Only execute trusted projects; use disposable credential-free runners for external
contributions. Path containment does not contain code executed by Flutter.

No model service or automatic upload is part of the alpha. Tool results are sent to
your MCP host; its model/provider privacy policy applies. Dependency resolution can
access the network. Do not include secrets in reports or public issues.

Report vulnerabilities using GitHub private vulnerability reporting if enabled.
If unavailable, open an issue requesting a private contact without exploit details
or credentials. Supported release scope is currently the alpha candidate only.
