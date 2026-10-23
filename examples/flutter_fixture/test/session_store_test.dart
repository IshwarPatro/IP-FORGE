import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/session_store.dart';

void main() {
  test('logout removes only the selected user token', () {
    final store = SessionStore();
    store.save('alice', 'a');
    store.save('bob', 'b');
    expect(store.tokenFor('alice'), 'a');
    store.logout('alice');
    expect(store.tokenFor('alice'), isNull);
    expect(store.tokenFor('bob'), 'b');
  });
}
