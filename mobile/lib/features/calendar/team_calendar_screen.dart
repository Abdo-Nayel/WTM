import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../core/theme/app_theme.dart';
import '../../models/calendar_event.dart';
import '../../providers/calendar_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_view.dart';
import '../../widgets/loading_view.dart';

class TeamCalendarScreen extends ConsumerWidget {
  const TeamCalendarScreen({super.key});

  Color _parseColor(String hex) {
    var h = hex.replaceAll('#', '');
    if (h.length == 6) h = 'FF$h';
    final value = int.tryParse(h, radix: 16);
    if (value == null) return AppTheme.teal;
    return Color(value);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(calendarProvider);
    final focused = state.focusedDay ?? DateTime.now();
    final selected = state.selectedDay ?? focused;
    final dayEvents = state.eventsForDay(selected);

    return Stack(
      children: [
        Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: Row(
                children: [
                  Text(
                    'Team calendar',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const Spacer(),
                  SegmentedButton<bool>(
                    segments: const [
                      ButtonSegment(value: false, label: Text('Month')),
                      ButtonSegment(value: true, label: Text('Week')),
                    ],
                    selected: {state.isWeekView},
                    onSelectionChanged: (_) {
                      ref.read(calendarProvider.notifier).toggleView();
                    },
                  ),
                ],
              ),
            ),
            if (state.isLoading && state.events.isEmpty)
              const Expanded(child: LoadingView(message: 'Loading events…'))
            else if (state.error != null && state.events.isEmpty)
              Expanded(
                child: ErrorView(
                  message: state.error!,
                  onRetry: () => ref
                      .read(calendarProvider.notifier)
                      .loadForMonth(focused),
                ),
              )
            else
              Expanded(
                child: RefreshIndicator(
                  color: AppTheme.teal,
                  onRefresh: () => ref
                      .read(calendarProvider.notifier)
                      .loadForMonth(focused),
                  child: ListView(
                    padding: const EdgeInsets.only(bottom: 88),
                    children: [
                      TableCalendar<CalendarEvent>(
                        firstDay: DateTime.utc(2020, 1, 1),
                        lastDay: DateTime.utc(2035, 12, 31),
                        focusedDay: focused,
                        selectedDayPredicate: (d) => isSameDay(d, selected),
                        calendarFormat: state.isWeekView
                            ? CalendarFormat.week
                            : CalendarFormat.month,
                        availableCalendarFormats: const {
                          CalendarFormat.month: 'Month',
                          CalendarFormat.week: 'Week',
                        },
                        eventLoader: state.eventsForDay,
                        startingDayOfWeek: StartingDayOfWeek.monday,
                        headerStyle: const HeaderStyle(
                          formatButtonVisible: false,
                          titleCentered: true,
                          titleTextStyle: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 16,
                          ),
                        ),
                        calendarStyle: CalendarStyle(
                          todayDecoration: BoxDecoration(
                            color: AppTheme.teal.withOpacity(0.25),
                            shape: BoxShape.circle,
                          ),
                          selectedDecoration: const BoxDecoration(
                            color: AppTheme.teal,
                            shape: BoxShape.circle,
                          ),
                          markerDecoration: const BoxDecoration(
                            color: AppTheme.tealLight,
                            shape: BoxShape.circle,
                          ),
                        ),
                        onDaySelected: (day, focusedDay) {
                          ref
                              .read(calendarProvider.notifier)
                              .setSelectedDay(day);
                          ref
                              .read(calendarProvider.notifier)
                              .setFocusedDay(focusedDay);
                        },
                        onPageChanged: (focusedDay) {
                          ref
                              .read(calendarProvider.notifier)
                              .setFocusedDay(focusedDay);
                          ref
                              .read(calendarProvider.notifier)
                              .loadForMonth(focusedDay);
                        },
                        calendarBuilders: CalendarBuilders(
                          markerBuilder: (context, day, events) {
                            if (events.isEmpty) return null;
                            return Positioned(
                              bottom: 1,
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: events.take(3).map((e) {
                                  return Container(
                                    width: 6,
                                    height: 6,
                                    margin: const EdgeInsets.symmetric(
                                      horizontal: 1,
                                    ),
                                    decoration: BoxDecoration(
                                      color: _parseColor(e.color),
                                      shape: BoxShape.circle,
                                    ),
                                  );
                                }).toList(),
                              ),
                            );
                          },
                        ),
                      ),
                      const Divider(height: 1),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                        child: Text(
                          DateFormat.yMMMEd().format(selected),
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      if (dayEvents.isEmpty)
                        const Padding(
                          padding: EdgeInsets.all(24),
                          child: EmptyState(
                            title: 'No events',
                            subtitle: 'Nothing scheduled for this day.',
                            icon: Icons.event_available_outlined,
                          ),
                        )
                      else
                        ...dayEvents.map(
                          (e) => _EventTile(
                            event: e,
                            color: _parseColor(e.color),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
          ],
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            heroTag: 'create_event',
            onPressed: () => _showCreateEventDialog(context, ref, selected),
            icon: const Icon(Icons.add),
            label: const Text('Event'),
          ),
        ),
      ],
    );
  }

  Future<void> _showCreateEventDialog(
    BuildContext context,
    WidgetRef ref,
    DateTime day,
  ) async {
    final titleCtrl = TextEditingController();
    var start = DateTime(day.year, day.month, day.day, 9);
    var end = DateTime(day.year, day.month, day.day, 10);
    var allDay = false;
    var color = AppTheme.teal;
    var saving = false;

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModal) {
            final bottom = MediaQuery.viewInsetsOf(ctx).bottom;
            return Padding(
              padding: EdgeInsets.fromLTRB(20, 12, 20, 20 + bottom),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'New event',
                      style: Theme.of(ctx).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: titleCtrl,
                      decoration: const InputDecoration(labelText: 'Title'),
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('All day'),
                      value: allDay,
                      onChanged: (v) => setModal(() => allDay = v),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Start'),
                      subtitle: Text(
                        allDay
                            ? DateFormat.yMMMd().format(start)
                            : DateFormat.yMMMd().add_jm().format(start),
                      ),
                      trailing: const Icon(Icons.edit_calendar),
                      onTap: () async {
                        final d = await showDatePicker(
                          context: ctx,
                          initialDate: start,
                          firstDate: DateTime(2020),
                          lastDate: DateTime(2035),
                        );
                        if (d == null) return;
                        var next = DateTime(
                          d.year,
                          d.month,
                          d.day,
                          start.hour,
                          start.minute,
                        );
                        if (!allDay) {
                          final t = await showTimePicker(
                            context: ctx,
                            initialTime: TimeOfDay.fromDateTime(start),
                          );
                          if (t != null) {
                            next = DateTime(
                              d.year,
                              d.month,
                              d.day,
                              t.hour,
                              t.minute,
                            );
                          }
                        }
                        setModal(() => start = next);
                      },
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('End'),
                      subtitle: Text(
                        allDay
                            ? DateFormat.yMMMd().format(end)
                            : DateFormat.yMMMd().add_jm().format(end),
                      ),
                      trailing: const Icon(Icons.edit_calendar),
                      onTap: () async {
                        final d = await showDatePicker(
                          context: ctx,
                          initialDate: end,
                          firstDate: DateTime(2020),
                          lastDate: DateTime(2035),
                        );
                        if (d == null) return;
                        var next = DateTime(
                          d.year,
                          d.month,
                          d.day,
                          end.hour,
                          end.minute,
                        );
                        if (!allDay) {
                          final t = await showTimePicker(
                            context: ctx,
                            initialTime: TimeOfDay.fromDateTime(end),
                          );
                          if (t != null) {
                            next = DateTime(
                              d.year,
                              d.month,
                              d.day,
                              t.hour,
                              t.minute,
                            );
                          }
                        }
                        setModal(() => end = next);
                      },
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Color'),
                      trailing: CircleAvatar(backgroundColor: color, radius: 12),
                      onTap: () async {
                        await showDialog(
                          context: ctx,
                          builder: (dCtx) => AlertDialog(
                            title: const Text('Pick color'),
                            content: SingleChildScrollView(
                              child: BlockPicker(
                                pickerColor: color,
                                onColorChanged: (c) => color = c,
                              ),
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(dCtx),
                                child: const Text('Done'),
                              ),
                            ],
                          ),
                        );
                        setModal(() {});
                      },
                    ),
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: saving
                          ? null
                          : () async {
                              if (titleCtrl.text.trim().isEmpty) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text('Title is required'),
                                    backgroundColor: AppTheme.danger,
                                  ),
                                );
                                return;
                              }
                              setModal(() => saving = true);
                              final hex =
                                  '#${(color.value & 0xFFFFFF).toRadixString(16).padLeft(6, '0')}';
                              final event = await ref
                                  .read(calendarProvider.notifier)
                                  .createEvent(
                                    title: titleCtrl.text.trim(),
                                    startAt: start,
                                    endAt: end,
                                    allDay: allDay,
                                    color: hex,
                                  );
                              if (!ctx.mounted) return;
                              setModal(() => saving = false);
                              if (event == null) {
                                final err = ref.read(calendarProvider).error ??
                                    'Failed to create event';
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text(err),
                                    backgroundColor: AppTheme.danger,
                                  ),
                                );
                                return;
                              }
                              Navigator.pop(ctx);
                            },
                      child: saving
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text('Create event'),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
    titleCtrl.dispose();
  }
}

class _EventTile extends StatelessWidget {
  const _EventTile({required this.event, required this.color});

  final CalendarEvent event;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final time = event.allDay
        ? 'All day'
        : '${DateFormat.jm().format(event.startAt)} – ${DateFormat.jm().format(event.endAt)}';

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.border),
      ),
      child: Row(
        children: [
          Container(
            width: 4,
            height: 40,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  event.title,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 2),
                Text(
                  time,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.slateMuted,
                  ),
                ),
                if (event.department != null && event.department!.isNotEmpty)
                  Text(
                    event.department!,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.slateMuted,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
