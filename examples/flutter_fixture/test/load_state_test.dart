import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/load_state.dart';

void main() {
  test('error ends loading and later success clears error', () async {
    final state = LoadState();
    await state.load(() async => throw Exception('offline'));
    expect(state.loading, isFalse);
    expect(state.error, 'Could not load');
    await state.load(() async => 'loaded');
    expect(state.loading, isFalse);
    expect(state.error, isNull);
    expect(state.value, 'loaded');
  });
}
