import 'package:flutter/material.dart';

import '../config.dart';
import '../l10n.dart';
import '../services/app_state.dart';

/// First-time setup: language → province → topics.
/// Also reused from the menu to change one of them ([only] = 0, 1 or 2).
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key, required this.state, this.only});
  final AppState state;
  final int? only;

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  static const red = Color(0xFFE8412C);
  late int step = widget.only ?? 0;
  late List<String> topics = List.of(widget.state.topics);

  AppState get st => widget.state;

  Future<void> _next() async {
    if (step == 2) await st.setTopics(topics);
    if (!mounted) return;
    if (widget.only != null) {
      Navigator.of(context).pop();
    } else if (step < 2) {
      setState(() => step++);
    } else {
      await st.finishOnboarding();
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: st,
      builder: (context, _) {
        final s = st.s;
        return Scaffold(
          backgroundColor: Colors.white,
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 28, 24, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text.rich(
                    const TextSpan(children: [
                      TextSpan(text: 'Canada '),
                      TextSpan(text: 'Shorts', style: TextStyle(color: red)),
                    ]),
                    style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.black),
                  ),
                  Text(s.t('tagline'), style: const TextStyle(color: Colors.black54, fontSize: 14)),
                  const SizedBox(height: 22),
                  if (widget.only == null)
                    Row(children: [
                      for (var i = 0; i < 3; i++)
                        Container(
                          width: 22,
                          height: 4,
                          margin: const EdgeInsets.only(right: 6),
                          decoration: BoxDecoration(
                              color: i <= step ? red : const Color(0xFFECECEC), borderRadius: BorderRadius.circular(2)),
                        ),
                    ]),
                  const SizedBox(height: 18),
                  Text(s.t(['langQ', 'provQ', 'topicsQ'][step]),
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colors.black)),
                  const SizedBox(height: 4),
                  Text(s.t(['langSub', 'provSub', 'topicsSub'][step]),
                      style: const TextStyle(fontSize: 14, color: Colors.black54)),
                  const SizedBox(height: 16),
                  Expanded(child: _body(s)),
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 52,
                    child: FilledButton(
                      style: FilledButton.styleFrom(
                          backgroundColor: red,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
                      onPressed: (step == 2 && topics.isEmpty) || (step == 1 && st.province == null && widget.only == null)
                          ? null
                          : _next,
                      child: Text(s.t(step == 2 && widget.only == null ? 'start' : 'next'),
                          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                    ),
                  ),
                  if (step == 1)
                    TextButton(
                      onPressed: () async {
                        await st.setProvince(null);
                        await _next();
                      },
                      child: Text(s.t('skip'), style: const TextStyle(color: Colors.black54)),
                    ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _option(String label, {required bool on, VoidCallback? onTap, String? badge}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: on ? const Color(0xFFFFF3F1) : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: BorderSide(color: on ? red : const Color(0xFFECECEC), width: 1.5),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Row(children: [
              Expanded(
                child: Text(label,
                    style: TextStyle(fontSize: 17, color: onTap == null ? Colors.black38 : Colors.black)),
              ),
              if (badge != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: const Color(0xFFF4F4F5), borderRadius: BorderRadius.circular(99)),
                  child: Text(badge, style: const TextStyle(fontSize: 12, color: Colors.black45)),
                ),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _body(S s) {
    if (step == 0) {
      return ListView(children: [
        for (final l in languages)
          _option(l.name,
              on: l.id == st.lang,
              badge: l.ready ? null : s.t('soon'),
              onTap: l.ready ? () => st.setLang(l.id) : null),
      ]);
    }
    if (step == 1) {
      return ListView(children: [
        for (final code in provinceCodes)
          _option(s.provinceName(code), on: code == st.province, onTap: () => st.setProvince(code)),
      ]);
    }
    return SingleChildScrollView(
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: [
          for (final id in topicIds)
            ChoiceChip(
              label: Text(s.topic(id)),
              selected: topics.contains(id),
              showCheckmark: false,
              selectedColor: red,
              backgroundColor: Colors.white,
              labelStyle: TextStyle(
                  fontSize: 15, color: topics.contains(id) ? Colors.white : Colors.black),
              shape: StadiumBorder(
                  side: BorderSide(color: topics.contains(id) ? red : const Color(0xFFECECEC), width: 1.5)),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              onSelected: (on) => setState(() {
                if (on) {
                  topics.add(id);
                } else {
                  topics.remove(id);
                }
              }),
            ),
        ],
      ),
    );
  }
}
