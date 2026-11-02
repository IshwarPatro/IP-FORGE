# Flutter MCP: progress and your next steps

## Phase 0 & Milestone 1 — Core Flutter Review Engine (Implemented)

Implemented:

- **Project Detection & Introspection (`forge/flutter/detect.py`)**: Locates `pubspec.yaml`, parses SDK constraints, detects target platforms, test suites, and identifies state management (Riverpod, Bloc, Provider, native) and cache libraries.
- **Review Policy & Configuration (`forge/flutter/policy.py`)**: Strict `.ip-forge.yaml` parser and schema validator, enforcing required checks, platform rules, cache rules, and configurable exit codes.
- **Isolated Execution Runner (`forge/flutter/runner.py`)**: Runs `flutter analyze` and `flutter test`, converting toolchain diagnostics and test assertion failures into truthful `Finding`, `CheckResult`, and `ReviewReport` models. Never infers success from missing tools or empty suites.
- **Reporting Engine (`forge/reports/formatter.py`)**: Generates standardized Markdown summary tables and machine-readable JSON for CI comments and PR/MR reviews.
- **MCP Tool Integration (`forge/mcp/flutter_tools.py`, `forge/mcp/server.py`)**: Exposes `inspect_flutter_project`, `run_flutter_checks`, and `get_flutter_report` via the unified MCP Server.
- **Unified Command-Line Interface (`forge/cli.py`)**: Ships `forge doctor`, `forge inspect [PATH]`, and `forge check [PATH] [--json] [--markdown]`.

- **Stdio Transport Protocol (`forge/mcp/stdio.py`)**: Implements newline-delimited JSON-RPC 2.0 protocol (`initialize`, `ping`, `tools/list`, `tools/call`), enabling direct integration with Claude Desktop, Cursor, Antigravity IDE, and standard MCP hosts.
- **Acceptance Test Suite (`tests/integration/test_acceptance_fixtures.py`)**: Gated against both healthy code (asserting `passed`) and deliberately seeded bugs (stale listener notifications and cross-account cache destruction, asserting `failed` with reproduced test failures).

Verification:

- Python Test Suite: **73 passed**, 0 failed (8 legacy embedding tests skipped).
- Stdio MCP Protocol: verified with end-to-end unit tests (`tests/unit/test_stdio_mcp.py`).
- Flutter Acceptance Fixtures: verified end-to-end (`tests/integration/test_acceptance_fixtures.py`).
- Flutter CLI `forge check examples/flutter_fixture`: passed with exit code `0`.

## What you need to do now

1. Send the absolute path to one Flutter app you own and can use for testing. A small app or disposable copy is ideal. Do not send credentials.
2. Tell me its state-management library and version if known (Riverpod, Bloc/Cubit, Provider, or another). We can inspect `pubspec.yaml` and `pubspec.lock` once you provide the path.
3. Identify its caching packages and intended behavior: what should be cached, how long, and what must be cleared on logout. “Not decided yet” is acceptable.
4. List three important user journeys, for example login → home, home → details → back, and logout → switch account.
5. Confirm whether Flutter web is already enabled and whether the app's primary code host is GitHub or GitLab.

You do not need to create PyPI accounts, install databases, configure AMD, or expose a public server at this stage. Flutter is already installed.

## Commands you can run

From the IP FORGE root:

```bash
PATH="$PWD/venv/bin:$PATH" venv/bin/python -m pytest tests -q
```

Run the Flutter fixture:

```bash
cd examples/flutter_fixture
flutter pub get
flutter analyze
flutter test
```

These Flutter tests run local fixture code and are unit/widget tests, not web/device end-to-end checks. Keep the generated fixture lockfile for reproducibility. Do not run the old autonomous demos against a real app as part of this migration.

Optional legacy embedding suite:

```bash
PATH="$PWD/venv/bin:$PATH" venv/bin/python -m pytest tests --run-rag
```

## Next phases

1. Finish Phase 0 acceptance fixtures and pilot policy.
2. Implement read-only workspace detection and the real stdio MCP adapter.
3. Add Dart analyzer integration and the first state/cache review rules.
4. Add controlled Flutter execution and registered web journeys.
5. Integrate GitHub/GitLab reports and public packaging.
6. Add visual/native checks and reviewed conflict resolution later.

The complete roadmap remains in `PUBLIC_MCP_IMPLEMENTATION_AND_RELEASE_PLAN.md`. Nothing has been committed, pushed, or published by this phase.

## 20 October follow-up

Fixed stdio tool responses dropping diagnostic output when a check failed.
Failed checks now retain both the error summary and detailed report, with
`isError=true`. Added regressions for failed reports and errors without output.
Targeted verification: 23 tests passed across stdio, Flutter tools, runner,
policy, and detection. This does not establish full MCP protocol conformance.

The optional model workstream still awaits the concise baseline result from AMD;
`docs/flutter-pilot-v2-baseline.json` is the earlier truncated-output run.
Continue that evaluation with the command in `FLUTTER_TRAINING_PILOT.md` before
more fine-tuning. No publication or deployment was performed.

## Local continuation: workspace and report behavior

- Flutter tools now resolve and enforce workspace containment, including absolute
  paths and symlink traversal. This is a path boundary, not OS isolation for tests.
- `get_flutter_report` returns the last in-memory report without executing checks.
  Reports are session-local snapshots; they do not automatically reflect later edits.
  With no report, the tool instructs the caller to run checks first.
- Explicit check overrides reject empty, duplicate, or blank lists.
- 41 targeted tests passed across MCP transport/tools, runner, policy, detection,
  and report contracts. No AMD service was needed.
- Read-only CLI inspection of `/Users/ishwar/Desktop/Apps/spacecraftarcade` succeeded:
  native state, no recognized cache package, one test file, all six platform folders.
  Package detection does not establish correct state/cache behavior. The app was
  not modified or executed by this inspection.

Local commands from the IP FORGE repository:

```sh
venv/bin/python -m forge.cli inspect /Users/ishwar/Desktop/Apps/spacecraftarcade
venv/bin/python -m forge.cli mcp --workspace /Users/ishwar/Desktop/Apps/spacecraftarcade
```

The MCP command waits for JSON-RPC requests from an agent host; it is not an
interactive terminal prompt. Client setup and real-app check results are still
pending. GPU model evaluation is paused due to insufficient Radeon credits.


## Real-app acceptance, 20 October

Ran `forge check --json` against a disposable copy of spacecraftarcade. Analyzer
and existing widget suite passed; CLI exit 0. Verified all 144 copied source
files still match the original app. Details: `SPACECRAFTARCADE_REVIEW.md`.
The current app is a counter starter with one test, so this is a pipeline
acceptance check, not evidence of cache or navigation coverage.
