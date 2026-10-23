import 'package:flutter/material.dart';

void main() => runApp(const FixtureApp());

class FixtureApp extends StatelessWidget {
  const FixtureApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            appBar: AppBar(title: const Text('Items')),
            body: TextButton(
              key: const Key('open-details'),
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => Scaffold(
                    appBar: AppBar(title: const Text('Details')),
                    body: const Text('Fixture item'),
                  ),
                ),
              ),
              child: const Text('Open item'),
            ),
          ),
        ),
      );
}
