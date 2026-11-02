# Flutter Review MCP: next phases and timeline

Prepared: 20 October 2026. Planning baseline: approximately **35% complete / 65% remaining** for the narrow public MVP, with roughly ±10 percentage points uncertainty. This is a scope-weighted engineering estimate, not measured code completion. Creating this plan does not increase it.

This document sequences the remaining work in [the implementation roadmap](PUBLIC_MCP_IMPLEMENTATION_AND_RELEASE_PLAN.md). It takes precedence over that document's older progress notes; feature scope remains unchanged.

## Target and assumptions

Deliver an installable local MCP that an existing agent can use to inspect a Flutter project, check declared state/cache rules, execute configured tests and web journeys, and report useful evidence on GitHub PRs and GitLab MRs.

Plan for **six working weeks, plus one to two weeks contingency**: approximately 30–40 focused developer-days. Assumes one developer working about five focused days a week, access to a representative Flutter app, and timely account setup. Assistant help can accelerate implementation but does not remove testing or account dependencies. At two or three working days per week, allow roughly 10–20 calendar weeks.

Illustrative schedule starts Monday 26 October 2026: beta candidate by 4 December; contingency through 18 December. These are estimates, not commitments. Work can start immediately; move dates if availability differs. Each phase must meet its gate before dependent work proceeds.

No AMD credits or further model training are required for this release. Initially support framework-native state / ChangeNotifier using existing fixtures; list other adapter rules as unsupported until validated. Package detection alone does not verify architecture.

## Current evidence

- CLI, project detection, policy schema, analyzer/test runner, JSON/Markdown reports, and initial MCP tools exist.
- Workspace containment and cached report handling have targeted tests; independent host interoperability remains unfinished.
- Spacecraftarcade analysis and its widget suite passed in a disposable copy. It is a counter starter, so it does not validate cache or complex navigation behavior.
- State/cache configuration is not yet a substantive review engine. Registered browser journeys and task-specific PR/MR reporting remain unfinished.
- Local MLX training and adapter reload work, but both base and trained model missed all three defects in the small development evaluation. The model must not decide whether a change is safe.

Evidence: [completion assessment](PROJECT_COMPLETION_STATUS.md), [app review](SPACECRAFTARCADE_REVIEW.md), [model evaluation](LOCAL_MODEL_EVALUATION.md), [dataset v3](FLUTTER_DATASET_V3.md).

## Phase schedule

| Phase | Target window | Effort | Deliverable and completion gate |
| --- | --- | --- | --- |
| 1. Truthful checks and policy foundation | 26–30 October | 5 days | Supported policy fields are enforced; unsupported checks and missing required checks cannot silently pass; runner outcomes and report identity tested |
| 2. State and cache checks | 2–6 November | 5 days | Narrow first adapter plus registered behavior tests detect seeded defects and accept clean/exception fixtures with inspectable evidence |
| 3. MCP and execution hardening | 9–13 November | 5 days | Independent client and two selected hosts can inspect/run/read reports; malformed requests survive; execution boundary documented and enforced |
| 4. Flutter web journeys | 16–20 November | 5 days | Configured browser journeys reproduce navigation/cache/render failures and preserve failure artifacts |
| 5. GitHub and GitLab CI | 23–27 November | 5 days | Healthy and broken PR/MR runs produce correct status and revision-bound report artifacts on both providers |
| 6. Packaging and public beta | 30 November–4 December | 5 days | Clean install outside checkout, host verification, source releases, package publication and discovery verification |
| Contingency | 7–18 December | 5–10 days | Resolve analyzer/version issues, browser flakes, packaging incompatibilities and account delays |

The critical dependency chain is policy/results → rules → MCP/execution → journeys → CI → release. Documentation and package cleanup can overlap; release testing cannot be skipped to keep a date.

## Phase 1 — make the core reliable

1. Inspect the current implementation and run the relevant existing tests; record baseline failures before edits.
2. Inventory every policy field. Mark each as implemented, unsupported or deferred. Validate check names, aliases, severities and required-check behavior.
3. Correct timeout, missing executable, compile error and assertion-failure reporting. Preserve raw diagnostics and distinguish inconclusive execution from a reproduced application defect.
4. Record revision, dirty-worktree state or source fingerprint, configuration hash and tool versions so reports identify what was actually checked.
5. Remove machine-specific SDK assumptions; resolve explicit SDK configuration and PATH with useful errors.
6. Add focused regression tests and rerun healthy/broken fixtures in disposable copies.

**Gate:** required work that did not execute never produces a successful review; CLI and report outcomes agree. A timeout is not described as a proven application bug.

**Your steps:** keep using the existing Mac and Flutter installation. Identify the first host you want to use and list three important flows in the intended application. The current counter starter is sufficient for smoke testing only.

## Phase 2 — implement useful state/cache review

1. Publish a small rule catalogue with rule ID, applicability, severity, evidence type, supported versions and explicit limitations.
2. Add a versioned Dart analyzer bridge where symbol/type information is necessary. Do not treat keyword matching as proof of lifecycle or ownership correctness.
3. Start with narrowly testable native-state/ChangeNotifier lifecycle and notification cases. Require healthy, defective and intentional-exception fixtures for each enabled static rule.
4. Map cache requirements to explicitly registered behavioral tests: expiry boundaries with a fake clock, account isolation, logout scope, refresh replacement and offline fallback.
5. Add asynchronous stale-response and loading/error recovery cases. Missing behavior tests mean unverified coverage, not a detected defect or a pass.
6. Connect findings and coverage to the shared runner so CLI and MCP use the same implementation.

**Gate:** seeded supported defects fail for the intended reason; healthy and allowed-exception fixtures pass. Reports state what was actually proven. Cache correctness cannot be inferred merely from use of a cache package.

**Scope fallback:** if broad static analysis exceeds the week, ship fewer explicitly named supported rules plus behavioral checks; defer additional adapters rather than claim support.

**Your steps:** confirm whether the real app will use native state, Provider, Riverpod or Bloc; define which data is private, expiry expectations and logout behavior. Native support remains the first implementation unless project evidence changes that choice.

## Phase 3 — make MCP reliable for another developer

1. Align the transport with the official SDK/protocol implementation and test it through an independent client.
2. Handle malformed JSON/requests, invalid arguments, unsupported methods, cancellation and tool failures without crashing the server. Keep protocol stdout free of logs.
3. Expose only the intended Flutter tools in the public entry point; audit legacy tools so they cannot bypass workspace or execution restrictions.
4. Separate read-only inspection from execution. Resolve paths and symlinks consistently; set timeouts, output limits and process cleanup.
5. Run trusted local tests in disposable workspaces; use an appropriately isolated, credential-free CI execution environment for untrusted contributions. A subprocess or copied folder alone is not a security sandbox.
6. Verify tool discovery, a healthy run, a failing run and cached report retrieval in two selected MCP hosts.

**Gate:** an independent user can get equivalent CLI/MCP findings, and failed tool responses retain actionable evidence. Document any execution restrictions that remain.

**Your steps:** install/configure the selected hosts when test instructions are ready. No model download is needed for these tools; your host agent supplies its own reasoning.

## Phase 4 — verify web flows

1. Implement web build and registered flow execution using a pinned, tested Flutter/browser setup.
2. Define real assertions for navigation/content, retry/loading recovery and cache refresh/logout. A page opening is not a passing journey.
3. Capture runtime exceptions and relevant Flutter render errors; retain console logs and screenshots on failure.
4. Add bounded waits, cleanup and explicit missing-browser/missing-test outcomes. Keep flaky retries visible.
5. Verify a healthy flow and separately seeded navigation, stale-data and render failures.

**Gate:** each supported failure is reproduced with useful artifacts. A mobile-only app reports web checks as not applicable; web success does not claim Android/iOS coverage.

**Your steps:** provide expected behavior for each registered flow and any synthetic test accounts needed. Keep production credentials out of fixtures.

## Phase 5 — test changes in CI

1. Build shared CLI-based jobs and example workflows for GitHub and GitLab.
2. Check the intended commit/merge revision and include source/target/tested SHAs in artifacts. Mark outdated reports as stale.
3. Run the relevant analysis, rules, unit/widget checks and registered web flows; upload JSON, Markdown and failure artifacts.
4. Keep contribution-code execution separate from token-bearing reporting jobs. Use least-privilege tokens and avoid exposing release credentials.
5. Publish a concise PR/MR summary or documented pipeline notification with links to evidence. Update existing summaries rather than posting duplicates.
6. Validate healthy and intentionally broken changes on both providers, including a contribution without trusted secrets.

**Gate:** a broken PR and MR fail correctly and link to useful evidence; a healthy change passes. Local YAML validation alone does not satisfy this gate.

**Your steps:** choose a GitLab namespace/project and ensure GitHub access works. Configure credentials using platform settings or a credential manager when needed; do not paste tokens into chat. Supply access and notification preferences before provider testing.

## Phase 6 — publish the beta

1. Separate core dependencies from optional MLX/ROCm, dashboard and legacy features. Build wheel and source archives; inspect their contents.
2. Include any Dart helper and required metadata; verify fresh installation outside the repository without local data/model folders.
3. Finish README, compatibility matrix, license, security/contribution guidance, sample policy and host setup examples.
4. Test the declared support matrix. Label untested OS/framework combinations explicitly rather than promising universal support.
5. Rehearse package release, select an available owned package name and configure authenticated publishing.
6. Publish matching reviewed source versions/tags to GitHub and GitLab; publish the tested package and verify installation.
7. Validate current MCP registry requirements, publish discovery metadata, and verify it points to the exact released package. Recheck provider documentation at implementation time.
8. Have a second person install it and diagnose a seeded Flutter regression using only public instructions.

**Gate:** public installation and host execution work without this checkout, a private key, AMD credits or a downloaded model. Record actual release URLs and versions; do not mark publication complete based on prepared files.

**Your steps:** settle license/ownership and public visibility before release; provide GitLab/PyPI access as needed and recruit one tester. Account delays move the release date.

## Optional model track — outside the release critical path

Allow an additional **2–4 weeks of dataset and evaluation work**, followed by a bounded training decision; a useful model is not guaranteed in that period.

1. Keep current weights, adapters, logs and evaluations unchanged for comparison.
2. Expand beyond ten training records with reviewed, licensed examples and executable tests for defects and repairs. Include healthy counterexamples and explicit requirements.
3. Group related code/bug families before splitting; remove structural near-duplicates. Keep an unseen test set out of prompt tuning and training decisions.
4. Evaluate the base model before another training run; define false-positive and defect-recall acceptance criteria in advance.
5. Run a small local MLX pilot and compare against the same baseline. Continue only if evidence justifies it.
6. If later integrated, expose model suggestions as advisory and preserve deterministic test evidence separately.

Do not increase epochs on the current tiny set as a substitute for data quality. The current local adapter detected 0/3 development defects, so further training is not a release gate.

## Deferred work and additional effort

- Native Android/iOS journeys and reviewed golden baselines: approximately 2–4 additional weeks, dependent on device/emulator access.
- Assisted conflict repair: approximately 2–3 additional weeks after verification is reliable. Reproduce in an isolated worktree, show a proposed patch and rerun checks; ambiguous behavior requires a human decision. No automatic merge.
- A hosted public multi-tenant MCP service and production monitoring are not in this plan. Public MVP means an installable local server used alongside an agent.

## Progress tracking and immediate next action

Track each phase as not started / in progress / verified, with test outputs and artifact links. Update [completion status](PROJECT_COMPLETION_STATUS.md) only when acceptance evidence changes; time spent or new training runs alone do not increase product completion.

**Next implementation session:** complete Phase 1's policy-field audit and runner outcome fixes, then add the first bounded state/cache checks. You do not need to launch an AMD instance, reinstall the model or start another training job.
