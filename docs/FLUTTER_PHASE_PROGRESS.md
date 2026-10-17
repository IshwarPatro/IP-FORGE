# Flutter MCP: progress and your next steps

## Phase 0 — foundation (in progress)

Implemented:

- Legacy tests run against a temporary dummy repository and temporary Chroma location.
- Legacy LLM health checks are forced offline in tests; approval endpoint unit tests mock commits.
- Governance tests no longer depend on execution order or shared session data.
- Eight legacy embedding tests are explicitly opt-in (`--run-rag`); they may require an embedding download. They are not replaced by fake semantic search.
- Initial strict Python policy/report contracts distinguish failed, missing, unsupported, and unexecuted checks from success.
- Ten contract test cases cover required checks, severity policy, and invalid/duplicate input.
- A minimal Flutter fixture covers TTL expiry, account separation/logout, and details/back navigation.

Verified reference toolchain: Flutter 3.35.7 / Dart 3.9.2 on this Mac. No SDK upgrade was performed. Flutter needed permission to update its existing SDK cache and retrieve fixture dependencies.

Verification:

- Python: 44 passed, 8 legacy embedding tests skipped by default.
- Flutter analyzer: no issues.
- Flutter fixture: 3 tests passed.

Still required before Phase 0 is complete:

- Select the pilot app and first state-management adapter.
- Add separate seeded broken fixtures and demonstrate that the acceptance checks detect them.
- Extend the fixture for loading/error/offline recovery, disposed-state behavior, and overflow.
- Confirm the first supported platform/toolchain matrix.

The Python policy is an initial internal contract. It does not yet load the full proposed `.ip-forge.yaml` schema. There is no working Flutter MCP checker or browser integration harness yet.

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
