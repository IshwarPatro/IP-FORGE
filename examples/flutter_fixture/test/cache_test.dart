import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/account_cache.dart';

void main() {
  test('fresh hit expires at the TTL boundary without sleeping', () {
    var time = DateTime.utc(2026);
    final cache = AccountCache(now: () => time, ttl: const Duration(minutes: 5));
    cache.put('alice', 'items', 'private');
    expect(cache.get('alice', 'items'), 'private');
    time = time.add(const Duration(minutes: 5));
    expect(cache.get('alice', 'items'), isNull);
  });

  test('account separation and logout preserve other account entries', () {
    final cache = AccountCache(now: () => DateTime.utc(2026), ttl: const Duration(minutes: 5));
    cache.put('alice', 'items', 'alice data');
    expect(cache.get('bob', 'items'), isNull);
    cache.put('bob', 'items', 'bob data');
    cache.logout('alice');
    expect(cache.get('alice', 'items'), isNull);
    expect(cache.get('bob', 'items'), 'bob data');
  });
}
