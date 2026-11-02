# Phase 0 reference fixture

A deliberately small Flutter app using framework-native navigation, with a fake-clock account cache. It does not choose the product's first state-management adapter.

Run `flutter pub get`, `flutter analyze`, and `flutter test` here.

Current acceptance coverage: expiry boundary, account isolation, logout cleanup, details/back navigation. These are unit/widget tests, not browser or mobile integration tests.

Pending Phase 0 cases: loading/error/offline recovery, disposed-state mutation, render overflow, and separate seeded broken variants. A complete login flow and supported web harness follow once the pilot architecture is selected. Do not interpret this fixture as a finished Flutter checker.
