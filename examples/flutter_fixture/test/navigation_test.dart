import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:forge_flutter_fixture/main.dart';

void main() {
  testWidgets('item opens details and back returns to list', (tester) async {
    await tester.pumpWidget(const FixtureApp());
    await tester.tap(find.byKey(const Key('open-details')));
    await tester.pumpAndSettle();
    expect(find.text('Fixture item'), findsOneWidget);
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('open-details')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
