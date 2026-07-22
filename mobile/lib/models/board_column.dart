class BoardColumn {
  const BoardColumn({
    required this.id,
    required this.name,
    this.position = 0,
    this.wipLimit,
    this.projectId,
    this.isDone = false,
  });

  final String id;
  final String name;
  final int position;
  final int? wipLimit;
  final String? projectId;
  final bool isDone;

  factory BoardColumn.fromJson(Map<String, dynamic> json) {
    return BoardColumn(
      id: (json['id'] ?? '').toString(),
      name: json['name'] as String? ?? '',
      position: json['position'] is int
          ? json['position'] as int
          : int.tryParse('${json['position'] ?? 0}') ?? 0,
      wipLimit: json['wip_limit'] is int
          ? json['wip_limit'] as int
          : int.tryParse('${json['wip_limit'] ?? ''}'),
      projectId: json['project_id']?.toString() ?? json['project']?.toString(),
      isDone: json['is_done'] == true || json['is_done_column'] == true,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'position': position,
        if (wipLimit != null) 'wip_limit': wipLimit,
        if (projectId != null) 'project_id': projectId,
        'is_done': isDone,
      };
}
