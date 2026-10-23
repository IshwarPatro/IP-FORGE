class SessionStore {
  final Map<String, String> _tokens = {};
  void save(String user, String token) => _tokens[user] = token;
  String? tokenFor(String user) => _tokens[user];
  void logout(String user) => _tokens.remove(user);
}
