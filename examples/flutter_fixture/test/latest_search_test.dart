import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/latest_search.dart';

void main() {
  test('latest request wins even when an older response arrives last', () async {
    final model = LatestSearch();
    final old = Completer<String>();
    final recent = Completer<String>();
    final first = model.search(old.future);
    final second = model.search(recent.future);
    recent.complete('new');
    await second;
    expect(model.result, 'new');
    old.complete('old');
    await first;
    expect(model.result, 'new');
  });
}
