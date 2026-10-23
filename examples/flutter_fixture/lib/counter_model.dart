import 'package:flutter/foundation.dart';

/// Native ChangeNotifier fixture; no third-party state library is required.
class CounterModel extends ChangeNotifier {
  int _count = 0;
  int get count => _count;

  void increment() {
    _count += 1;
    notifyListeners();
  }
}
