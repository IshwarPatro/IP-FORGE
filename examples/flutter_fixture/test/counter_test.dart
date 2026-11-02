import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/counter_model.dart';

void main() {
  test('increment updates state and notifies a subscriber', () {
    final model = CounterModel();
    addTearDown(model.dispose);
    var notifications = 0;
    model.addListener(() => notifications += 1);
    model.increment();
    expect(model.count, 1);
    expect(notifications, 1);
  });
}
