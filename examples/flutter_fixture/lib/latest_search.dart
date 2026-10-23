class LatestSearch {
  int _request = 0;
  String? result;

  Future<void> search(Future<String> response) async {
    final request = ++_request;
    final value = await response;
    if (request != _request) return;
    result = value;
  }
}
