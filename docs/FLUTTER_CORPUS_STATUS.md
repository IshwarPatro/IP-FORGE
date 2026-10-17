# Flutter corpus status

Updated: 15 October 2026. No training has run.

## Acquired source

- Repository: https://github.com/flutter/website
- Pinned commit: `d0f80ce71784dc65d01dbc9748bf3244e59660b8`
- Source checkout: `data/flutter_docs/source`
- Raw records: 2,108
- Markdown files: 1,226
- Dart files: 877
- HTML files: 5
- Text bytes: 22,992,047

The full clone timed out; a sparse text/code checkout succeeded. Media assets were intentionally excluded. Raw records include source URLs and SHA-256 hashes. Data is ignored by Git.

## Retrieval baseline

- Distinct documentation pages: 663
- Exact duplicate pages excluded: 44
- Heading sections: 6,447
- Pages flagged with unresolved template syntax: 506
- Search engine: local SQLite FTS5 (lexical); no embedding model or GPU required.

```bash
python3 scripts/prepare_flutter_corpus.py
python3 scripts/build_flutter_retrieval.py
python3 scripts/build_flutter_retrieval.py --query 'offline first cache repository'
```

The final command currently ranks the official offline-first architecture section first. This is a smoke check, not a retrieval-quality benchmark. Heading splitting preserves fenced code; tests cover that and source attribution/filtering/deduplication.

## Coverage and remaining work

This inventories the selected official website source, not all rendered Flutter material. API references, Dart language documentation, external libraries, videos, and historical versions are not included. Frontmatter is removed for retrieval and code-excerpt annotations are removed where examples are already embedded. Other templates remain unresolved and are counted, not claimed to be rendered. Chunk lengths are not yet bounded for a model tokenizer.

Before training: resolve required includes; retain document links/attribution; verify SDK-version metadata; group near-duplicates; prepare instruction/review examples with executable outcomes; hold out independent evaluation tasks; measure tokens and costs.

## License handling

The downloaded root LICENSE says CC BY 3.0 for content with BSD code conditions, while the public docs site footer identifies CC BY 4.0 with BSD-3-Clause samples. These differing notices are retained rather than reconciled by assumption. Inspect applicable per-file/subtree notices before redistributing a curated dataset. The raw corpus is local and has not been uploaded or published.
