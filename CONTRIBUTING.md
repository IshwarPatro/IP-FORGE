# Contributing

Start with the Flutter alpha scope in README. Keep legacy and training dependencies optional.

Install `python -m pip install '.[dev]'`. Run the standalone release smoke test with
`python scripts/release_smoke.py`; it exercises the installed CLI and an SDK client.
The broader legacy suite currently needs `.[legacy,dev]` and isolates its working
repository through `tests/conftest.py`. Do not run untrusted Flutter tests with secrets.

Add positive, negative and missing-capability cases for new checks. Findings must
separate static suspicion from reproduced failures. Never describe missing tests
as successful behavior verification. Open a PR with the behavior change and validation.
