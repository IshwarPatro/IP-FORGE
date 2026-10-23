class LoadState {
  bool loading = false;
  String? error;
  String? value;

  Future<void> load(Future<String> Function() fetch) async {
    loading = true;
    error = null;
    try {
      value = await fetch();
    } catch (_) {
      error = 'Could not load';
    } finally {
      loading = false;
    }
  }
}
