# IP FORGE: Flutter Review MCP — implementation and public release plan

Updated: 14 October 2026  
Status: proposed roadmap; new commands, tools, and configuration below are target interfaces, not implemented features.  
Scope decision: this document supersedes the general-purpose autonomous engineering roadmap. It retains public GitHub/GitLab distribution and installation alongside existing agents.

## 1. Product purpose

Build a local MCP server and a shared command-line checking engine that help developers answer:

> Does this Flutter change follow our state-management and caching rules, pass our checks, and preserve our important screens and user journeys?

An existing agent uses MCP tools to inspect findings, explain them, and propose fixes. CI runs the same engine automatically on pull requests/merge requests and publishes reports. The MCP process itself is not an always-on monitoring or notification service.

### Target users and platforms

- Flutter mobile teams using Android/iOS and optionally the same project's Flutter web target.
- GitHub pull requests and GitLab merge requests.
- Existing agents with local stdio MCP support.
- Initial runtime verification: unit/widget tests and explicitly configured Flutter web journeys.
- Later verification: golden baselines and Android/iOS emulator/device journeys.

Generic React/Vue/Next.js application checking is outside this scope. A mobile-only project remains supported for static/unit/widget checks; web jobs are marked not applicable rather than forced onto it.

### What “proper” means

Validate a project's declared architecture and behavior, not one universal library choice. Bloc/Cubit, Riverpod, Provider, and framework-native state can all be appropriate. Package detection is only a starting point; the developer confirms the policy and allowed exceptions.

Static analysis can identify some definite defects and some suspicious patterns. Rendering and business-flow correctness require execution and meaningful assertions. Missing tests must be reported as missing coverage, never as evidence that a flow works.

## 2. Release scope

| Milestone | Deliverables | Release gate |
| --- | --- | --- |
| M0: foundation | Isolated tests, reusable workspace services, real MCP, truthful results | SDK client initializes and invokes a read-only tool |
| M1: Flutter review MVP | Project detection, version-aware state/cache review, analyze/unit/widget checks, configured web journeys, JSON/Markdown report | Seeded defects are detected and healthy fixtures do not fail incorrectly |
| M2: public installable release | GitHub/GitLab CI reports, source release, PyPI package, agent setup, MCP Registry entry | Another developer installs it and checks a real Flutter MR |
| M3: visual and mobile verification | Golden testing, layout matrix, Android/iOS journeys | Reproducible visual/flow failures with inspectable artifacts |
| M4: assisted conflict repair | Isolated merge reproduction, agent-proposed resolutions, validation, reviewed publishing | No unresolved or unverified resolution is presented as safe to merge |

MVP reports likely state/caching issues and runs configured tests. It does not guarantee that every architectural or caching bug can be detected. Deep rule support should start with one versioned state-management adapter selected from the first real pilot project; other libraries receive generic checks and an explicit unsupported-rule notice until their adapters are tested.

### Explicitly deferred or removed

- General-purpose code generation and the six-agent autonomous loop.
- Mandatory AMD/cloud inference, performance comparisons, or internal LLM credentials.
- Python AST/Chroma RAG as the Flutter analysis engine.
- A mandatory dashboard, Redis, or PostgreSQL.
- Automatic merge, production deployment, store publishing, or silent conflict fixes.
- Public hosted filesystem access and a multi-tenant hosted service.
- Continuous production monitoring. Scheduled CI smoke tests may be added later.

The old code can remain as clearly labeled experimental legacy functionality while reusable pieces are extracted. Do not delete it as part of a documentation-only scope change.

## 3. What can be reused, and what must change

The earlier audit found 42 passing Python tests, successful TypeScript checking, and 9 frontend lint errors. Those results describe the old prototype, not Flutter readiness. The earlier completion percentage does not transfer to this new scope; re-estimate after M1 acceptance tests exist.

| Existing area | Decision | Required work |
| --- | --- | --- |
| `forge/mcp/fs_tools.py` | Reuse carefully | Explicit workspace binding, bounded reads, denied secrets, path safety tests |
| `forge/mcp/server.py` | Replace adapter | Implement actual SDK-based MCP protocol and stdio transport |
| `forge/mcp/terminal_tools.py` | Refactor | Flutter verification profiles and execution isolation; no unrestricted shell tool |
| `forge/mcp/git_tools.py` | Refactor | Consistent root, worktrees, exact commits, complete diffs, merge inspection |
| `forge/config.py` | Simplify | Per-project policy and explicit user config; logs to stderr |
| `forge/rag/ast_parser.py` | Not suitable for Dart | Introduce a Dart analyzer helper; Python AST cannot parse Flutter code |
| `forge/agents/*`, `forge/orchestrator/*` | Defer | Existing host agent provides reasoning and remediation |
| `forge/api/main.py`, `dashboard/` | Optional legacy UI | Keep out of default release until contracts and governance are repaired |
| Deployment/AMD scripts | Archive/document as optional legacy | Not a requirement for Flutter MCP |

Do not expose legacy `/mcp/execute` commit routes or simulated approval flows through the new distribution. Their prior governance weaknesses must not become a second route around the new policy.

## 4. Target architecture

```text
Existing agent ── stdio MCP ─┐
                            ├── shared Flutter checking engine
GitHub/GitLab CI ── CLI ─────┘      ├── workspace and revision resolver
                                  ├── Dart analyzer/rule adapters
                                  ├── state/cache policy evaluation
                                  ├── isolated Flutter test runner
                                  ├── diff/merge inspector
                                  └── structured report and artifacts
                                                │
                                   CI reporting job with limited credentials
                                                │
                                   PR/MR summary and pipeline status
```

Suggested layout:

```text
forge/
  cli.py
  mcp/server.py
  workspace/                 # roots, worktrees, Git revision identity
  flutter/
    detect.py
    policy.py
    analyzer_bridge.py
    rules/                   # versioned state/cache adapters
    runner.py
    flows.py
  reports/                   # JSON schema and Markdown rendering
  integrations/              # GitHub/GitLab reporting
  security/                  # permissions and execution profiles
analyzer/                    # Dart helper using supported analyzer APIs
examples/flutter_fixture/    # small healthy app with deterministic tests
examples/ci/                 # tested GitHub/GitLab templates
examples/agent-configs/
tests/unit/
tests/integration/
tests/fixtures/              # seeded state/cache/flow failures
```

Keep result generation independent of the transport. A CLI report and an MCP report for the same revision/configuration must have the same findings.

## 5. Step 0 — establish safe tests and acceptance fixtures

1. Move Git/file-mutating tests into temporary independent repositories. The existing approval test must not attempt a commit in the developer checkout.
2. Mock network and model dependencies in unit tests. Test the new core without an LLM, Chroma, or dashboard.
3. Create one small Flutter fixture with login, item listing, details, logout, and a repository-backed cache.
4. Add healthy fixtures and separately seeded failures: disposed state mutation, stale cache, cross-account cache reuse, missing error state, broken navigation, failed request recovery, and a layout overflow.
5. Capture known findings and expected test outcomes. Keep intentionally broken fixtures out of the default healthy app test target.
6. Decide which Python/Flutter/Dart/browser versions are supported and pin the first reference environment.

**Done when:** checks are repeatable, do not mutate the developer's repository, and distinguish real defects from intentionally valid exceptions.

## 6. Step 1 — define policy and truthful result schemas

### Project configuration

Implement a validated `.ip-forge.yaml` schema. The following is a proposed shape:

```yaml
schema_version: 1
flutter_root: .
platforms: [android, ios, web]
state_management:
  adapter: riverpod
  exceptions: []
cache:
  policy: stale_while_revalidate
  requirements:
    account_scoped: true
    clear_private_data_on_logout: true
    max_age_seconds: 300
checks:
  analyze: required
  unit_widget: required
  web_build: required
  web_flows: required
flows:
  - id: login_to_details
    test: integration_test/login_to_details_test.dart
    platforms: [web]
  - id: logout_clears_account
    test: integration_test/logout_test.dart
    platforms: [web]
report:
  fail_on: [error]
  fail_on_required_missing: true
```

Values are project decisions, not universal rules. Not every cache needs the same TTL or logout behavior; distinguish private account data from public shared content. A YAML entry does not implement a journey: each listed test must exist and assert the behavior.

### Result contract

Every run includes repository identity, base/head/tested SHAs, configuration hash, toolchain versions, selected checks, duration, and artifacts. Every finding includes rule ID/version, category, severity, file/line, evidence, confidence, remediation guidance, and whether it is static inference or a reproduced failure.

Use explicit check states: `passed`, `failed`, `not_run`, `unsupported`, `inconclusive`, `not_applicable`, and `cancelled`. “No tests found,” unavailable Chrome, unsupported library versions, or missing emulator must never become `passed`.

Proposed CLI exit codes: `0` required checks passed, `1` confirmed policy/test failure, `2` configuration/infrastructure/required-coverage failure. Preserve nonzero failures through report generation and uploads.

Suppressions require rule ID, scope, rationale, and optional expiry. Track existing debt separately from new findings; do not hide new failures by regenerating a baseline automatically.

**Done when:** machine-readable and human-readable reports explain both findings and coverage limits.

## 7. Step 2 — ship real MCP and a read-only CLI

1. Use a tested version of the official Python MCP SDK. Implement initialization, tool schemas, calls, and lifecycle using its supported API.
2. Start with stdio and an explicit absolute workspace root.
3. Move logs from stdout to stderr so they cannot corrupt protocol messages.
4. Make project configuration explicit; do not automatically load credentials from a scanned repository's `.env`.
5. Add `--help`, `--version`, `doctor`, and `mcp` commands.
6. Add SDK-client subprocess tests for initialization, listing, calls, malformed inputs, cancellation, and shutdown.
7. Verify through MCP Inspector and at least two real host agents.

### Proposed tools

| Tool | Purpose | Permission |
| --- | --- | --- |
| `inspect_flutter_project` | Detect roots, SDK constraints, dependencies, platforms, existing checks | Read |
| `review_state_management` | Apply supported architecture rules with evidence | Read |
| `review_caching` | Evaluate declared cache behavior and available tests | Read |
| `inspect_change` | Diff exact base/head revisions and identify affected areas | Read |
| `run_flutter_checks` | Run configured analyze/unit/widget/build profiles | Execute opt-in |
| `run_flow_tests` | Run named registered journeys on a supported target | Execute opt-in |
| `get_report` | Retrieve findings, check coverage, and artifact references | Read |
| `inspect_merge_conflicts` | Reproduce merge in a disposable worktree | Workspace mutation opt-in |
| `propose_resolution` | Store an agent-supplied candidate patch for review, later phase | No original-checkout mutation |
| `verify_resolution` | Validate an approved candidate in isolation, later phase | Edit/execute opt-in |

Read-only means no source edits; it does not automatically authorize executing repository code. Treat execution and editing as separate permissions. Do not expose arbitrary shell, commit, or merge tools in the MVP.

**Done when:** a standard MCP host can inspect a Flutter project without a custom REST client or model key.

Protocol references: [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), [official Python SDK](https://github.com/modelcontextprotocol/python-sdk).

## 8. Step 3 — detect Flutter projects and implement Dart analysis

1. Locate `pubspec.yaml`, Flutter SDK constraints, `pubspec.lock`, analysis options, app entry points, tests, and platform directories. Handle monorepos through explicitly selected app roots.
2. Detect state/cache packages and resolved versions. Declared dependencies alone are not proof that an architecture is used correctly.
3. Build a small Dart helper using analyzer APIs to return structured declarations, references, ownership/lifecycle evidence, and diagnostics to Python.
4. Pin helper compatibility and test it against supported SDK versions. Avoid fragile regular-expression-only correctness checks.
5. Use regex/text searches only as labeled hints where semantic analysis is unavailable.
6. Distribute the Dart helper as package data with its own dependency metadata; resolve/cache it separately from the target app so setup does not rewrite the app's pubspec or lockfile.
7. Document first-run dependency downloads and offline behavior. Report SDK mismatch instead of installing or upgrading the user's SDK silently.

**Done when:** semantic rules identify actual symbol usage, locations are accurate, and unsupported SDK/library versions produce explicit limits.

## 9. Step 4 — implement state-management reviews

### Initial rule families

| Review area | Evidence to inspect | Verification needed |
| --- | --- | --- |
| Resource ownership | Controller/subscription ownership and cleanup | Lifecycle test or high-confidence analyzer rule |
| State after disposal | Async callbacks and widget/provider lifetime | Navigate-away test during in-flight work |
| Loading/error/empty states | State definitions and UI handling | Widget tests for each required state |
| UI/business separation | Declared project boundaries and dependencies | Policy rule with documented exceptions |
| Duplicate requests | Repeated initialization or rebuild-triggered side effects | Request-count assertion |
| Stale async results | Out-of-order responses and cancellation behavior | Controlled response-order test |
| Broad rebuilds | State subscriptions and scope | Hint first; measured rebuild evidence before claiming a performance defect |

Implement adapters against the actual package versions in fixtures. Begin with the pilot project's selected library, then add Bloc/Cubit, Provider, and other Riverpod versions through separate tested adapters. Do not assume every controller must be disposed by the widget if its ownership belongs elsewhere.

**Done when:** each blocking rule has positive, negative, and exception fixtures; speculative findings remain advisory.

## 10. Step 5 — implement caching reviews

1. Identify cache owners and data flow: repository/service, memory, persistent database, HTTP cache, image cache, and any configured browser deployment cache.
2. Compare implementation with project requirements: expiry, mutation invalidation, refresh, offline reads, write synchronization, bounded storage, and data migration.
3. Review account/tenant key separation and clearing of private cached data on logout or account switch.
4. Check concurrency: deduplicated requests, stale responses overwriting newer data, retry loops, and offline queued-write policy.
5. Add fake-clock tests for TTL and fake-network tests for fresh/stale/offline/recovery behavior.
6. Keep dependency/build caching in CI separate from application-data caching in reports.
7. For Flutter web, inspect the actual hosting/CDN/service-worker configuration when present. Do not assume a particular generated worker exists or infer HTTP cache headers from Dart code alone.

Minimum cache test matrix: cold load, fresh hit, expiry, mutation invalidation, offline hit, offline miss, reconnect, logout, account switch, and storage failure. Mark irrelevant cases explicitly rather than requiring all patterns for every application.

Follow project policy with Flutter's [offline-first guidance](https://docs.flutter.dev/app-architecture/design-patterns/offline-first) as design context. Architecture recommendations are not proof that one cache strategy fits every app.

**Done when:** reports separate proven stale-data/account-leak failures from missing policy or missing test evidence.

## 11. Step 6 — implement verification profiles and flow testing

### MVP profiles

- Dart formatting check, without rewriting files.
- Flutter analyzer diagnostics.
- Unit and widget tests, with structured results and optional coverage.
- Flutter web build, only when the target is supported and required.
- Explicitly registered Flutter web integration journeys.

Common command building blocks include:

```bash
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test --coverage
flutter build web
```

Construct argv based on detected directories and configuration; do not run missing `test/` paths blindly. Dependency resolution must occur in the isolated workspace under the pinned toolchain. Existing lockfiles should not be silently updated.

The web journey runner must implement and test the supported integration harness for the selected Flutter/browser version, including any driver/browser service requirements. Do not assume a single `flutter test` command runs every web integration suite. Native Flutter integration tests should be the main app-flow harness; external browser tooling can complement deployment smoke tests, but DOM selectors alone are insufficient for every Flutter rendering mode.

### Journey definition

Each journey specifies entry route, controlled initial data, actions, expected state/navigation, error/offline cases, and cleanup. Examples:

- Login succeeds and opens home; invalid login shows a useful error.
- Home opens details and back navigation returns correctly.
- Refresh after a mutation shows updated data.
- Offline mode shows cached data or the declared offline UI.
- Logout prevents previous-account data appearing after account switch.
- A deep link to a protected route applies the declared authentication policy.

Use stable keys/semantics and deterministic fixtures. No production credentials or live payment actions. Capture failed assertion, runtime exception, test identity, logs, and screenshots when supported. Record what actually ran; a web build passing does not prove a journey passed.

Flutter distinguishes [unit, widget, and integration testing](https://docs.flutter.dev/testing/overview). Use the supported [integration-test harness](https://docs.flutter.dev/cookbook/testing/integration/introduction) for the chosen target.

**Done when:** a seeded navigation failure and a stale-cache journey fail reproducibly, with artifacts an agent can inspect.

## 12. Step 7 — execute safely and preserve user work

1. Bind all services to a validated workspace; reject traversal, symlink escape, secret-file access, and Git internal mutation through file tools.
2. Use temporary copies or task worktrees for dependency resolution, builds, tests, and patch verification. Never alter the user's active checkout or lockfile unexpectedly.
3. Test execution runs project-controlled code. A command allowlist is not a sandbox.
4. Prefer nonprivileged disposable CI/container workers for Linux/web checks, mounting only the workspace and necessary caches. Do not mount the Docker socket, home directory, or credentials into jobs.
5. Use isolated macOS workers for later iOS execution; document that a Linux container cannot provide iOS simulator validation.
6. Separate dependency-download access from the test phase; restrict network and allow only explicit test services where feasible.
7. Bound runtime, memory, output, artifact size, and subprocess lifetime; cancel descendants as well as the parent process.
8. If robust isolation is unavailable locally, require explicit trusted-project execution opt-in. Keep read-only analysis usable and explain the limitation.
9. Do not let model arguments or repository instructions widen permissions.

**Done when:** sentinel tests verify workspace containment and missing secret inheritance, and cancellation leaves no worker processes behind.

## 13. Step 8 — check pull requests/merge requests in CI and notify

### Shared pipeline

1. Resolve immutable base/head SHAs and fetch enough history for a reliable diff.
2. Determine whether testing the source head or an actual proposed merge result. Record both input SHAs and the tested SHA in the report.
3. Inspect changed files and affected Flutter roots. Use broader suites for dependency/navigation/shared-state changes; a narrow diff cannot justify skipping all regression coverage.
4. Run fast state/cache/analyzer checks, then required unit/widget and web-flow jobs.
5. Export versioned JSON, Markdown, test results, logs, and screenshots. Add a tested JUnit converter where needed rather than labeling raw Flutter output as JUnit.
6. Preserve report artifacts even on failure; preserve the failing job status too.
7. Publish one updateable PR/MR summary per run/head SHA with failures, links, tested target, unsupported checks, and coverage gaps.
8. Reject stale results as merge approval evidence after new commits arrive. Support retries without duplicate comments.

### GitHub

Use pull-request checks with read-only permissions for untrusted code. A separate trusted reporting job may use narrowly scoped credentials to post results after validating repository/run identity and treating artifacts as untrusted data. Never execute PR-controlled code with privileged `pull_request_target` credentials. Optional comments may be unavailable on forks; required status and downloadable artifacts remain useful.

### GitLab

Configure merge-request jobs and required artifacts. Source-branch MR pipelines do not prove that the merged code works. Use merged-results pipelines where available, or explicitly construct a disposable merge candidate and label it correctly. If it cannot merge, report conflicts and block merge validation. See [GitLab MR pipeline behavior](https://docs.gitlab.com/ci/pipelines/merge_request_pipelines/).

### Notification policy

MVP notifications are CI status plus PR/MR summaries. No email/Slack/webhook integration is required initially. Later destinations must be explicitly configured with minimal credentials. Deduplicate messages, redact secrets, and keep raw logs in access-controlled artifacts.

### CI/CD boundary

Gate an existing Flutter web deployment on required checks; do not introduce production deployment in the MCP. Preview-environment smoke tests can verify actual route loading and asset availability. Production deployment and promotion remain separately authorized pipeline stages; artifact cache keys include SDK, OS, and lockfile identity.

**Done when:** a deliberately broken MR gets a failing status and useful report on both platforms, without exposing release secrets to its code.

## 14. Step 9 — add rendering and mobile checks after MVP

1. Add golden/widget tests for selected critical screens and states.
2. Pin Flutter version, fonts, locale, pixel ratio, viewport, and platform used for baselines.
3. Exercise representative screen sizes, text scaling, themes, loading/error/empty states, and overflow detection.
4. Store expected/current/diff images on failure. A visual difference is a review finding, not automatically a product defect.
5. Require human review for baseline updates; never update goldens merely to make CI green.
6. Add Android emulator journeys and then iOS simulator journeys with documented host/runtime requirements.
7. Report platform coverage honestly: passing web tests does not prove native plugins or Android/iOS flows work.
8. Keep flaky retries visible; do not silently turn repeated failure into success through retries.

**Done when:** seeded render and native-flow failures are reproducible under the declared environment.

## 15. Step 10 — assist conflict resolution after verification is reliable

1. Reproduce the merge using immutable source/target SHAs in a disposable worktree; leave the user's current checkout untouched.
2. Return conflicted files, base/ours/theirs evidence, related state/cache/navigation symbols, and relevant tests to the host agent.
3. The host agent proposes a resolution; IP FORGE validates and applies it only within the task worktree under edit permission.
4. Check for unresolved index entries and conflict markers, then rerun analysis, relevant suites, web build, and required journeys.
5. Regenerate generated Dart files using the project's pinned generator instead of hand-editing generated output. Resolve manifest intent first; regenerate/validate lockfiles through the package manager.
6. Escalate binary, schema/data migration, conflicting business behavior, and ambiguous state ownership cases for human decisions.
7. Show the exact resulting patch and verification coverage. Tests passing is necessary evidence, not a guarantee of semantic correctness.
8. Bind any publishing approval to exact source/target SHAs and patch hash; invalidate it if either branch moves.
9. If publishing is enabled, commit only reviewed files to an approved branch and return the actual commit/PR/MR URL. Failures remain failures. Never automatically merge into the target branch.

**Done when:** a simple fixture conflict is resolved and tested, while an ambiguous conflict stays blocked for a human decision.

## 16. Step 11 — package and document the public MCP

1. Keep Python as the orchestrating package; bundle/version the Dart helper and its metadata deliberately.
2. Select an available PyPI distribution name. Examples below retain `ip-forge`; confirm ownership before release.
3. Add `[project.scripts]` mapping `ip-forge` to `forge.cli:main` and explicit package discovery. Exclude legacy dashboards, local data, credentials, and fixtures from runtime artifacts unless intentionally packaged.
4. Make model/database dependencies unnecessary for this scope. Use tested dependency bounds and reproducible CI lockfiles.
5. Provide `doctor` checks for Python, Flutter/Dart SDK, browser, selected adapter, runner capabilities, and project config. Installation must not silently download a full Flutter SDK.
6. Build wheel and sdist; verify archive contents and fresh installation outside the source checkout. Ensure the Dart helper is included and runnable from the installed package.
7. Add a real license, `CONTRIBUTING.md`, `SECURITY.md`, changelog, example policy, permission/privacy documentation, and compatibility matrix.
8. Test supported Python/OS/Flutter versions. Document limited execution capabilities separately from basic server compatibility.

Proposed user commands, valid only after implementation/publication:

```bash
uvx --from ip-forge==0.2.0 ip-forge doctor --repo /absolute/path/to/flutter_app
uvx --from ip-forge==0.2.0 ip-forge check --repo /absolute/path/to/flutter_app --profile mr --output ./forge-report
```

The check command requires an explicitly configured execution permission/profile. A read-only MCP example for hosts accepting this JSON shape:

```json
{
  "mcpServers": {
    "ip-forge-flutter": {
      "command": "uvx",
      "args": [
        "--from", "ip-forge==0.2.0", "ip-forge", "mcp",
        "--repo", "/absolute/path/to/flutter_app", "--read-only"
      ]
    }
  }
}
```

Adapt configuration to each host; not every agent uses `mcpServers`, and browser-only hosts may not launch a local subprocess. Use real absolute paths and explicit executable paths if desktop PATH resolution fails. Users install Flutter and uv separately. Basic tool inspection needs no internal model key; the user's host agent may have its own inference requirements.

## 17. Step 12 — publish to GitHub and GitLab

The existing local `origin` is `https://github.com/IshwarPatro/IP-FORGE.git`. Verify remote access, branch names, visibility, and history before pushing. This document performs no publication.

1. Update README to this Flutter scope and label unsupported features clearly.
2. Review tracked files and history for credentials/private data; ignored files may still be tracked. Rotate exposed credentials if found.
3. Add license and contributor/security docs; review third-party assets and bundled analyzer licensing.
4. Implement `.github/workflows/ci.yml` and `.gitlab-ci.yml` using shared scripts. Test Python core, Dart helper, fixtures, protocol, package installation, and selected Flutter checks.
5. Push a feature branch to the existing GitHub remote, review it, and merge after checks pass.
6. Create an empty GitLab project without a conflicting initial commit. Keep GitHub canonical initially; document where contributions belong.
7. Add a separate GitLab remote using the real namespace, then push reviewed branches/tags without force or mirror deletion.

Inspection commands:

```bash
git status --short
git remote -v
git branch --show-current
git fetch origin
```

After a reviewed release commit on `main`, and only if version `0.2.0` is unused:

```bash
git switch main
git pull --ff-only origin main
git tag -a v0.2.0 -m "IP FORGE Flutter Review MCP beta"
git push origin main
git push origin v0.2.0
git remote add gitlab https://gitlab.com/YOUR_NAMESPACE/IP-FORGE.git
git push gitlab main
git push gitlab v0.2.0
```

Skip `remote add` if that remote already exists; replace branch/version/namespace with reviewed values. Authenticate through a credential manager or SSH, never a token in a documented remote URL. GitHub and GitLab releases should refer to the same commit/artifacts. Git source mirroring does not synchronize issues, PRs, MRs, or release metadata automatically.

Publishing references: [GitHub existing source](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github), [GitLab project creation](https://docs.gitlab.com/user/project/).

## 18. Step 13 — publish PyPI artifacts and MCP discovery

1. Establish ownership of the package name and configure PyPI Trusted Publishing for one protected release workflow. Use GitHub as publisher and GitLab for verification initially to avoid duplicate uploads.
2. Build and inspect artifacts in a clean output directory:

```bash
python -m build
python -m twine check dist/*
```

3. Rehearse on TestPyPI and install the exact candidate wheel in a fresh environment. Check helper inclusion and protocol execution, not just Python import success.
4. Publish the tested artifacts to production PyPI. Verify installation from production and capture a real Flutter fixture report.
5. Keep package version, tag, release notes, helper version, and registry entry consistent. Issue new patch versions for corrections rather than trying to replace a published version.
6. Install the official `mcp-publisher` CLI and generate current-schema `server.json` with `mcp-publisher init`.
7. Choose an owned namespace, provisionally `io.github.IshwarPatro/ip-forge`, validating exact naming through the publisher. Point it to the exact PyPI version, stdio entry point, and required workspace argument.
8. Include the matching ownership marker in the packaged README before building the release:

```html
<!-- mcp-name: io.github.IshwarPatro/ip-forge -->
```

9. Authenticate, validate, and publish metadata:

```bash
mcp-publisher login github
mcp-publisher validate
mcp-publisher publish
```

10. Verify the registry entry and installation instructions from a second environment. Registry publication is discovery, not automatic installation or endorsement by every host.

Sources: [Python packaging](https://packaging.python.org/en/latest/tutorials/packaging-projects/), [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/adding-a-publisher/), [MCP Registry publishing](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx), [package verification](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/package-types.mdx), [uv tools](https://docs.astral.sh/uv/guides/tools/). Recheck release-time schemas and commands against the installed publisher version.

## 19. Implementation PR order and effort

| PR | Work | Exit evidence |
| --- | --- | --- |
| 01 | Scope/config/result schemas, isolated tests, Flutter fixtures | Healthy and seeded failure expectations |
| 02 | Workspace binding, real stdio MCP, minimal CLI | Real SDK client smoke test |
| 03 | Flutter detection and packaged Dart analyzer helper | Accurate versioned symbol diagnostics |
| 04 | First state adapter and generic lifecycle rules | Positive/negative/exception fixtures |
| 05 | Cache policy and behavior checks | Fake-clock/network/account-switch tests |
| 06 | Isolated analyze/unit/widget/web-build profiles | Complete truthful check reports |
| 07 | Registered web journeys and artifacts | Broken navigation/cache flow reproduced |
| 08 | GitHub/GitLab change checks and notifications | Failed MR status with report links |
| 09 | Package, compatibility docs, CI, public release | Fresh install and registry verification |
| 10 | Golden and native-platform journeys | Reproducible visual/mobile regressions |
| 11 | Assisted conflict repair and reviewed publishing | Safe isolated resolution plus human gate |

For one experienced developer, plan approximately 4–7 weeks for a narrow tested MVP/public beta, then 2–4 weeks for visual/mobile coverage and 2–3 weeks for assisted conflict repair. These are estimates, not commitments; analyzer depth, supported library versions, and available Flutter test coverage determine effort. Start with one pilot application rather than promising all libraries and platforms at launch.

## 20. Acceptance checklist

### Public MVP

- [ ] Installable Python package includes the correct Dart helper and starts outside the checkout.
- [ ] Two MCP hosts discover and call tools with no internal LLM dependency.
- [ ] Project state/cache policy is explicit and versioned.
- [ ] Unsupported frameworks/versions and missing tests are reported honestly.
- [ ] State/cache findings include source evidence and distinguish inference from reproduced defects.
- [ ] Analyzer, unit/widget checks, and configured web journeys execute and report failures correctly.
- [ ] No checks mutate the user's working tree unexpectedly.
- [ ] Execution permissions are distinct from read-only access.
- [ ] CI records exact reviewed/tested SHAs and never treats stale results as current.
- [ ] A broken GitHub PR and GitLab MR receive useful failing reports.
- [ ] Untrusted code cannot access notification/release credentials.
- [ ] GitHub/GitLab source releases, PyPI artifacts, and MCP metadata are verified.
- [ ] Another developer can install it and diagnose a real Flutter regression.

### Later capabilities

- [ ] Golden changes require review; mobile results identify the actual tested device/platform.
- [ ] Conflict resolution runs in isolation and includes full validation evidence.
- [ ] Ambiguous resolutions remain blocked; no automatic merge or production deployment exists.
- [ ] Publishing a fix returns an actual commit/PR/MR identifier and handles failure honestly.

Success means a developer can ask their existing agent, “Check this Flutter merge request,” and receive evidence-backed state/cache findings, executed test results, and clear warnings about broken or untested flows—then use that evidence to make a reviewed fix.


## 21. Optional documentation/model workstream — 15 October update

At the user’s request, official Flutter documentation acquisition and a model experiment are now being prepared alongside this roadmap. The deterministic checker and local MCP remain independent of training. See [model/data plan](FLUTTER_MODEL_AND_DATA_PLAN.md), [corpus status](FLUTTER_CORPUS_STATUS.md), and [provided AMD notebook setup](AMD_NOTEBOOK_NEXT_STEPS.md). Use the event-provided environment before considering paid GPU rental. Raw documentation download and lexical indexing are complete for the selected source snapshot; fine-tuning is not started.


### Flutter model pilot progress

Both AMD synthetic fit checks passed (128 and 512 tokens; batch one).
The first fixture-based dataset builder is implemented in
`scripts/prepare_flutter_pilot.py`; procedure, limitations, and remaining gates
are in [FLUTTER_TRAINING_PILOT.md](FLUTTER_TRAINING_PILOT.md).
This optional workstream does not complete the MCP protocol or CI integration.
Training remains pending tokenizer validation, dataset expansion, and evaluation.
