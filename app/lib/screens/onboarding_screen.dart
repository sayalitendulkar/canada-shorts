import 'package:flutter/material.dart';

import '../config.dart';
import '../services/app_state.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key, required this.state});
  final AppState state;

  @override
  Widget build(BuildContext context) {
    final s = state.s;
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 24),
            Text(s.t('appName'), style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(s.t('welcome'), style: theme.textTheme.titleMedium),
            const SizedBox(height: 32),
            Text(s.t('chooseLang'), style: theme.textTheme.titleSmall),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'en', label: Text('English')),
                ButtonSegment(value: 'fr', label: Text('Français')),
              ],
              selected: {state.lang},
              onSelectionChanged: (v) => state.setLang(v.first),
            ),
            const SizedBox(height: 32),
            Text(s.t('chooseProvince'), style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            Text(s.t('provinceHint'), style: theme.textTheme.bodySmall),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final code in provinceCodes)
                  ChoiceChip(
                    label: Text(s.provinceName(code)),
                    selected: state.province == code,
                    onSelected: (on) => state.setProvince(on ? code : null),
                  ),
              ],
            ),
            const SizedBox(height: 40),
            FilledButton(
              onPressed: state.finishOnboarding,
              child: Padding(padding: const EdgeInsets.all(12), child: Text(s.t('start'))),
            ),
          ],
        ),
      ),
    );
  }
}
