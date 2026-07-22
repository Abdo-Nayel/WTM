import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/project_provider.dart';

Future<void> showCreateProjectSheet(BuildContext context) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (_) => const CreateProjectSheet(),
  );
}

class CreateProjectSheet extends ConsumerStatefulWidget {
  const CreateProjectSheet({super.key});

  @override
  ConsumerState<CreateProjectSheet> createState() => _CreateProjectSheetState();
}

class _CreateProjectSheetState extends ConsumerState<CreateProjectSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _keyCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  Color _color = AppTheme.teal;
  bool _saving = false;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _keyCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  void _suggestKey(String name) {
    if (_keyCtrl.text.isNotEmpty) return;
    final words = name.trim().split(RegExp(r'\s+'));
    final key = words
        .where((w) => w.isNotEmpty)
        .take(3)
        .map((w) => w[0].toUpperCase())
        .join();
    if (key.isNotEmpty) {
      _keyCtrl.text = key;
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final hex =
        '#${(_color.value & 0xFFFFFF).toRadixString(16).padLeft(6, '0')}';
    final project = await ref.read(projectProvider.notifier).create(
          name: _nameCtrl.text.trim(),
          key: _keyCtrl.text.trim().toUpperCase(),
          description: _descCtrl.text.trim(),
          color: hex,
        );
    if (!mounted) return;
    setState(() => _saving = false);
    if (project == null) {
      final err = ref.read(projectProvider).error ?? 'Failed to create project';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(err), backgroundColor: AppTheme.danger),
      );
      return;
    }
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Created ${project.key}')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 12, 20, 20 + bottom),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'New project',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _nameCtrl,
                decoration: const InputDecoration(labelText: 'Name'),
                textCapitalization: TextCapitalization.words,
                onChanged: _suggestKey,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Name is required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _keyCtrl,
                decoration: const InputDecoration(
                  labelText: 'Key',
                  hintText: 'e.g. WTM',
                ),
                textCapitalization: TextCapitalization.characters,
                validator: (v) {
                  if (v == null || v.trim().isEmpty) return 'Key is required';
                  if (v.trim().length > 10) return 'Max 10 characters';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _descCtrl,
                decoration: const InputDecoration(
                  labelText: 'Description (optional)',
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Color'),
                trailing: CircleAvatar(backgroundColor: _color, radius: 14),
                onTap: () async {
                  await showDialog(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      title: const Text('Pick color'),
                      content: SingleChildScrollView(
                        child: BlockPicker(
                          pickerColor: _color,
                          onColorChanged: (c) => _color = c,
                        ),
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text('Done'),
                        ),
                      ],
                    ),
                  );
                  setState(() {});
                },
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: _saving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Create project'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
