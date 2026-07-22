class Workspace {
  const Workspace({
    required this.id,
    required this.name,
    this.description = '',
    this.defaultKeyPrefix = 'WTM',
    this.role,
    this.memberCount,
  });

  final String id;
  final String name;
  final String description;
  final String defaultKeyPrefix;
  final String? role;
  final int? memberCount;

  factory Workspace.fromJson(Map<String, dynamic> json) {
    return Workspace(
      id: (json['id'] ?? '').toString(),
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      defaultKeyPrefix: json['default_key_prefix'] as String? ?? 'WTM',
      role: json['role'] as String?,
      memberCount: json['member_count'] is int
          ? json['member_count'] as int
          : int.tryParse('${json['member_count'] ?? ''}'),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'description': description,
        'default_key_prefix': defaultKeyPrefix,
        if (role != null) 'role': role,
        if (memberCount != null) 'member_count': memberCount,
      };
}
