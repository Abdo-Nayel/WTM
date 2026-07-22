class User {
  const User({
    required this.id,
    required this.email,
    this.firstName = '',
    this.lastName = '',
    this.username = '',
  });

  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String username;

  String get displayName {
    final name = '$firstName $lastName'.trim();
    if (name.isNotEmpty) return name;
    if (username.isNotEmpty) return username;
    return email;
  }

  String get initials {
    if (firstName.isNotEmpty && lastName.isNotEmpty) {
      return '${firstName[0]}${lastName[0]}'.toUpperCase();
    }
    if (email.isNotEmpty) return email[0].toUpperCase();
    return '?';
  }

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: _asString(json['id']),
      email: json['email'] as String? ?? '',
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      username: json['username'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'first_name': firstName,
        'last_name': lastName,
        'username': username,
      };

  static String _asString(dynamic v) {
    if (v == null) return '';
    return v.toString();
  }
}
