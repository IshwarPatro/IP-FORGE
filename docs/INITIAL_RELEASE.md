# Initial GitHub alpha: 0.2.0a1

Updated 24 October 2026. Alpha source is published on the release branch; no tagged release yet.

## Included

Flutter dependency/test inventory; analyzer and unit/widget execution; JSON and
Markdown reports; SDK stdio with Flutter-only tools and opt-in execution; core
package without model/database dependencies; source installation instructions;
package CI and a consumer Flutter workflow template.

## Excluded

State/cache correctness rules, web journeys, automatic PR/MR comments, native
visual testing, conflict repair, hosted MCP, reliable trained reviewer. Reports
currently lack complete revision/configuration identity. Advanced policy declarations the alpha cannot enforce now stop before execution
with an unsupported result; use the minimal configuration in README. Timeouts and
some compile failures still need finer diagnostic classification.

## Release procedure

1. Review `git diff` and intentionally select new source, tests, examples and docs.
   Preserve unrelated local work. Do not use a blind `git add .`.
2. Review staged changes and repository history for credentials/private artifacts.
   Do not include model weights, local datasets, virtual environments or egg-info.
3. Build with `python -m build`, install the wheel into a fresh Python 3.11+
   environment and run `python scripts/release_smoke.py` using that environment.
4. Run the Flutter core tests and trusted fixture acceptance tests. Run the
   GitHub matrix and try two actual desktop MCP hosts before broader claims.
5. Push a reviewed release branch to GitHub and review CI. Create a pre-release
   tag `v0.2.0a1` only if unused and attach the verified wheel/source archive.
6. Verify installation from the exact published commit, update README's pending
   publication note and record the real URL here. No PyPI/registry release yet.

The MIT license follows the existing repository README's declared MIT choice.
Historical third-party data and documentation are not relicensed by this file.
The GitLab integration and full beta remain in the longer roadmap.

## Validation record

Local verification passed: 49 existing core/regression tests; built wheel installed in an
isolated Python 3.12 environment; CLI invoked outside the checkout; independent
SDK client initialization, tool inventory, invalid arguments, traversal rejection,
failed-check reports and cached retrieval; raw stdout JSON-RPC framing; pip check.
Archives exclude model/data/environment artifacts. SDK tested: 1.30.0.

Artifacts are in `dist/`; hashes and limitations are recorded in
[alpha-release-validation.json](alpha-release-validation.json). GitHub hosted CI passed all five jobs. Two desktop hosts and a tagged release remain unverified.

Installed-wheel Flutter acceptance also passed: a disposable healthy fixture
returned exit 0; removing notifyListeners reproduced a widget failure with exit 1.
See [acceptance evidence](alpha-flutter-acceptance.json). This candidate is ready for contributor testing,
not a claim that the full product is finished.


## GitHub verification — 24 October 2026

Published commit: `022c9cabbb827f08d36b10531c26f96600a19810` on
`release/flutter-alpha-0.2.0a1`.
[CI run](https://github.com/IshwarPatro/IP-FORGE/actions/runs/39996995988):
all four Linux/macOS Python 3.11/3.12 package jobs and the Linux Flutter
acceptance job completed successfully. No merge or tag was created.

Next: verify in two desktop hosts, then review the branch for a GitHub prerelease.

Installation from the exact GitHub commit into the isolated Python 3.12 test
environment passed, followed by installed CLI and SDK-client smoke checks.
