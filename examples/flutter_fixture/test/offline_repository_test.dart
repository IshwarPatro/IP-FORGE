import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/offline_repository.dart';

void main() {
  test('successful refresh replaces cache and failure falls back', () async {
    final repo = OfflineRepository()..cached = 'old';
    expect(await repo.load(() async => 'fresh'), 'fresh');
    expect(await repo.load(() async => throw Exception('offline')), 'fresh');
  });
  test('failure without cache propagates', () async {
    final repo = OfflineRepository();
    await expectLater(repo.load(() async => throw Exception('offline')), throwsException);
  });
}
