class KeyCache {
  final Map<String, String> _values = {};
  void write(String key, String value) => _values[key] = value;
  String? read(String key) => _values[key];
  void invalidate(String key) => _values.remove(key);
}
