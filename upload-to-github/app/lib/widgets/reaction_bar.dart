import 'package:flutter/material.dart';

import '../models/story.dart';
import '../services/app_state.dart';

/// A row of emoji reactions under each story. One reaction per story; tapping
/// the same one again takes it back. No login, nothing personal is collected.
/// For now the choice is kept on this phone only (shared totals come later).
class ReactionBar extends StatelessWidget {
  const ReactionBar({super.key, required this.story, required this.state});
  final Story story;
  final AppState state;

  static const reactions = [
    ('like', '👍'),
    ('love', '❤️'),
    ('wow', '😮'),
    ('sad', '😢'),
    ('angry', '😡'),
  ];
  static const red = Color(0xFFE8412C);

  @override
  Widget build(BuildContext context) {
    final s = state.s;
    final cs = Theme.of(context).colorScheme;
    final mine = state.reactionFor(story);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(s.t('react'), style: TextStyle(fontSize: 12, color: cs.onSurfaceVariant)),
        const SizedBox(height: 6),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            for (final (id, emoji) in reactions)
              _Chip(
                emoji: emoji,
                label: s.t('r_$id'),
                on: mine == id,
                onTap: () => state.react(story, id),
              ),
          ],
        ),
      ],
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.emoji, required this.label, required this.on, required this.onTap});
  final String emoji;
  final String label;
  final bool on;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Tooltip(
      message: label,
      child: Semantics(
        button: true,
        selected: on,
        label: label,
        child: InkWell(
          borderRadius: BorderRadius.circular(99),
          onTap: onTap,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            padding: EdgeInsets.symmetric(horizontal: on ? 12 : 10, vertical: 6),
            decoration: BoxDecoration(
              color: on ? ReactionBar.red.withValues(alpha: 0.12) : cs.surfaceContainerHighest.withValues(alpha: 0.6),
              borderRadius: BorderRadius.circular(99),
              border: Border.all(color: on ? ReactionBar.red : Colors.transparent, width: 1.2),
            ),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              AnimatedScale(
                scale: on ? 1.25 : 1.0,
                duration: const Duration(milliseconds: 180),
                curve: Curves.easeOutBack,
                child: Text(emoji, style: const TextStyle(fontSize: 18)),
              ),
              if (on) ...[
                const SizedBox(width: 6),
                Text(label,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: ReactionBar.red)),
              ],
            ]),
          ),
        ),
      ),
    );
  }
}
