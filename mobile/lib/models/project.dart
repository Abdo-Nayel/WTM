class Project {
  const Project({
    required this.id,
    required this.name,
    required this.key,
    this.description = '',
    this.color = '#0F766E',
    this.workspaceId,
  });

  final String id;
  final String name;
  final String key;
  final String description;
  final String color;
  final String? workspaceId;

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: (json['id'] ?? '').toString(),
      name: json['name'] as String? ?? '',
      key: json['key'] as String? ?? '',
      description: json['description'] as String? ?? '',
      color: json['color'] as String? ?? '#0F766E',
      workspaceId: json['workspace_id']?.toString() ??
          json['workspace']?.toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'key': key,
        'description': description,
        'color': color,
        if (workspaceId != null) 'workspace_id': workspaceId,
      };
}
