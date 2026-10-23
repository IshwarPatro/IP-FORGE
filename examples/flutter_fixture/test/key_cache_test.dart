import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/key_cache.dart';

void main() {
  test('invalidating one key preserves others and allows refresh', () {
    final cache = KeyCache();
    cache.write('one', 'old');
    cache.write('two', 'keep');
    cache.invalidate('one');
    expect(cache.read('one'), isNull);
    expect(cache.read('two'), 'keep');
    cache.write('one', 'new');
    expect(cache.read('one'), 'new');
  });
}
