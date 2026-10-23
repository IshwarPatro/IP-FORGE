/// Small reference fixture, not a production cache implementation.
class AccountCache {
  AccountCache({required this.now, required this.ttl});
  final DateTime Function() now;
  final Duration ttl;
  final Map<(String, String), (String, DateTime)> _entries = {};

  void put(String account, String key, String value) {
    _entries[(account, key)] = (value, now().add(ttl));
  }

  String? get(String account, String key) {
    final entry = _entries[(account, key)];
    if (entry == null) return null;
    if (!now().isBefore(entry.$2)) {
      _entries.remove((account, key));
      return null;
    }
    return entry.$1;
  }

  void logout(String account) {
    _entries.removeWhere((key, _) => key.$1 == account);
  }
}
