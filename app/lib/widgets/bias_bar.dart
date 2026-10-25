import 'package:flutter/material.dart';

import '../l10n.dart';
import '../models/story.dart';

/// "▬ Covered by 3 outlets (1 left, 1 centre, 1 right)"
class CoverageLine extends StatelessWidget {
  const CoverageLine({super.key, required this.bias, required this.s});
  final BiasMix bias;
  final S s;

  static const leftColor = Color(0xFF2B6CB0);
  static const centreColor = Color(0xFF8A8F98);
  static const rightColor = Color(0xFFC53030);

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    final sides = bias.left + bias.centre + bias.right;
    final parts = <String>[
      if (bias.left > 0) '${bias.left} ${s.t('left')}',
      if (bias.centre > 0) '${bias.centre} ${s.t('centre')}',
      if (bias.right > 0) '${bias.right} ${s.t('right')}',
      if (bias.official > 0) '${bias.official} ${s.t('official')}',
    ];
    return Row(
      children: [
        if (sides > 0)
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: SizedBox(
                width: 54,
                height: 5,
                child: Row(children: [
                  if (bias.left > 0) Expanded(flex: bias.left, child: Container(color: leftColor)),
                  if (bias.centre > 0) Expanded(flex: bias.centre, child: Container(color: centreColor)),
                  if (bias.right > 0) Expanded(flex: bias.right, child: Container(color: rightColor)),
                ]),
              ),
            ),
          ),
        Expanded(
          child: Text(
            s.covered(bias.total) + (parts.isEmpty ? '' : ' (${parts.join(', ')})'),
            style: TextStyle(fontSize: 12, color: muted),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
