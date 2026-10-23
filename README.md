# IP FORGE — Flutter Review MCP

**0.2.0a1: initial alpha candidate.** Connect a local Flutter project to an MCP agent to inspect its dependencies, run Flutter analysis and unit/widget tests, and read evidence-backed reports.

This release does **not** certify state-management architecture or caching correctness. Dedicated rules, browser journeys, automated PR/MR comments and conflict repair are planned. Existing tests only establish the behavior they assert. Model training is experimental and is not required to install or use the MCP.

## Install from source

Requires Python 3.11+; install Flutter separately for `check`. macOS is the locally tested platform; CI configuration covers Python 3.11/3.12 on Linux and macOS. Other platforms are unverified.

```sh
git clone https://github.com/IshwarPatro/IP-FORGE.git
cd IP-FORGE
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
ip-forge --version
```

These instructions use the release files in this checkout; until pushed, the remote may still contain the older prototype. No PyPI release is claimed. After publication, prefer a reviewed release tag/commit over a moving branch. `forge` remains an alias for `ip-forge`.

Do not install `requirements.txt` for the alpha: that file serves the legacy application. The default package needs no GPU, model, database, dashboard or API key.

## Use with your Flutter project

```sh
ip-forge inspect /absolute/path/to/flutter_app
ip-forge doctor /absolute/path/to/flutter_app
ip-forge check /absolute/path/to/flutter_app --json > report.json
ip-forge check /absolute/path/to/flutter_app --markdown > report.md
```

Put Flutter on PATH or set `FLUTTER_ROOT` to its SDK directory. CLI checks also accept `--flutter-bin /absolute/path/to/flutter`. Run `flutter pub get` in your trusted app first.

Optional `.ip-forge.yaml` in your app root:

```yaml
schema_version: 1
required_checks: [analyze, unit_widget]
fail_on: [error]
```

Exit codes: `0` selected required checks passed; `1` failed check/policy severity; `2` required checks unavailable or incomplete. Configuration errors are fatal. Only `analyze` and `unit_widget` are supported checks in this alpha. Advanced state/cache, flow, platform-selection and nested-root policies are rejected as unsupported before execution. Use the minimal policy above until those features are implemented.

**Execution runs project code with your account's permissions.** It may write Flutter build/cache files and access network or credentials available to that process. Use trusted projects or a separately isolated, credential-free environment. Workspace path confinement is not an OS sandbox.

## Connect to an agent

For a host supporting `mcpServers` configuration, replace both paths below with actual absolute paths:

```json
{
  "mcpServers": {
    "ip-forge": {
      "command": "/absolute/path/to/IP-FORGE/.venv/bin/ip-forge",
      "args": ["mcp", "--workspace", "/absolute/path/to/flutter_app"]
    }
  }
}
```

The default tools are `inspect_flutter_project` and `get_flutter_report`. To enable `run_flutter_checks` for trusted code, append `"--allow-execution"` to `args`. Set `FLUTTER_ROOT` in the host process environment if its PATH differs from your terminal. Restart the server after changing configuration.

Ask your agent: “Inspect this Flutter project and list its state/cache packages and tests.” With execution enabled: “Run the configured Flutter checks and explain any failures.” Inspection detects packages; it does not prove correct usage. Reports are session-local snapshots and may be stale after edits. Reading a report never reruns tests.

The public CLI uses the official MCP Python SDK, constrained to its 1.x API. Host-specific installation interfaces vary; two desktop-host acceptance tests remain a release checklist item. Legacy transport/API modules are experimental and are not the public entry point.

## Integrate into CI

Use the same `ip-forge check ... --json` command after installing this package and your pinned Flutter SDK. Preserve its exit status and upload the report even on failure. See [consumer CI example](examples/ci/flutter-review.yml). Automatic PR comments and GitLab MR integration are not included yet.

## Development and release

- [Release checklist and verification](docs/INITIAL_RELEASE.md)
- [Next phases and timeline](docs/NEXT_PHASE_PLAN_AND_TIMELINE.md)
- [Completion assessment](docs/PROJECT_COMPLETION_STATUS.md)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)
- [Optional model evaluation](docs/LOCAL_MODEL_EVALUATION.md)

Earlier documents and dashboard/orchestrator modules describe the original hackathon prototype. They are outside the supported alpha scope. MIT license; see [LICENSE](LICENSE).
