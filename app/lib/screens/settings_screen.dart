import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config.dart';
import '../services/app_state.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.state});
  final AppState state;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final s = state.s;
        return Scaffold(
          appBar: AppBar(title: Text(s.t('settings'))),
          body: ListView(
            children: [
              ListTile(
                title: Text(s.t('language')),
                trailing: SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'en', label: Text('EN')),
                    ButtonSegment(value: 'fr', label: Text('FR')),
                  ],
                  selected: {state.lang},
                  onSelectionChanged: (v) => state.setLang(v.first),
                ),
              ),
              ListTile(
                title: Text(s.t('province')),
                trailing: DropdownButton<String?>(
                  value: state.province,
                  items: [
                    DropdownMenuItem<String?>(value: null, child: Text(s.t('none'))),
                    for (final c in provinceCodes)
                      DropdownMenuItem<String?>(value: c, child: Text(s.provinceName(c))),
                  ],
                  onChanged: state.setProvince,
                ),
              ),
              SwitchListTile(
                title: Text(s.t('darkMode')),
                value: state.darkMode,
                onChanged: state.setDark,
              ),
              const Divider(),
              ListTile(title: Text(s.t('about')), subtitle: Text(s.t('aboutText'))),
              ListTile(
                leading: const Icon(Icons.mail_outline),
                title: Text(s.t('contact')),
                subtitle: const Text(contactEmail),
                onTap: () => launchUrl(Uri(scheme: 'mailto', path: contactEmail)),
              ),
              ListTile(
                leading: const Icon(Icons.privacy_tip_outlined),
                title: Text(s.t('privacy')),
                onTap: () => launchUrl(Uri.parse(privacyUrl)),
              ),
            ],
          ),
        );
      },
    );
  }
}
