import 'package:flutter/material.dart';

import '../l10n.dart';
import '../models/story.dart';

/// "8 sources · Left 3 · Centre 3 · Right 2" with a proportional bar.
class BiasBar extends StatelessWidget {
  const BiasBar({super.key, required this.bias, required this.s});
  final BiasMix bias;
  final S s;

  static const leftColor = Color(0xFF2B6CB0);
  static const centreColor = Color(0xFF8A8F98);
  static const rightColor = Color(0xFFC53030);

  @override
  Widget build(BuildContext context) {
    final sides = bias.left + bias.centre + bias.right;
    final small = Theme.of(context).textTheme.labelSmall;
    final count = '${bias.total} ${bias.total == 1 ? s.t('source') : s.t('sources')}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (sides > 0)
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: SizedBox(
              height: 6,
              child: Row(children: [
                if (bias.left > 0) Expanded(flex: bias.left, child: Container(color: leftColor)),
                if (bias.centre > 0) Expanded(flex: bias.centre, child: Container(color: centreColor)),
                if (bias.right > 0) Expanded(flex: bias.right, child: Container(color: rightColor)),
              ]),
            ),
          ),
        const SizedBox(height: 4),
        Text(
          [
            count,
            if (bias.left > 0) '${s.t('left')} ${bias.left}',
            if (bias.centre > 0) '${s.t('centre')} ${bias.centre}',
            if (bias.right > 0) '${s.t('right')} ${bias.right}',
            if (bias.official > 0) '${s.t('official')} ${bias.official}',
          ].join(' · '),
          style: small,
        ),
        if (bias.blindspot != null)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(
              s.t(bias.blindspot == 'mostly_left' ? 'blindLeft' : 'blindRight'),
              style: small?.copyWith(fontStyle: FontStyle.italic),
            ),
          ),
      ],
    );
  }
}
