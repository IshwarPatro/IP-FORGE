class OfflineRepository {
  String? cached;

  Future<String> load(Future<String> Function() fetch) async {
    try {
      final fresh = await fetch();
      cached = fresh;
      return fresh;
    } catch (_) {
      if (cached != null) return cached!;
      rethrow;
    }
  }
}
