import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config.dart';
import '../services/app_state.dart';

/// About, contact (required by Google Play for news apps), privacy, dark mode.
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
          appBar: AppBar(
            backgroundColor: const Color(0xFF111111),
            foregroundColor: Colors.white,
            title: Text(s.t('about')),
          ),
          body: ListView(
            children: [
              Padding(
                padding: const EdgeInsets.all(20),
                child: Text(s.t('aboutText'), style: const TextStyle(fontSize: 15, height: 1.5)),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.mail_outline),
                title: Text(s.t('contact')),
                subtitle: const Text(contactEmail),
                onTap: () => launchUrl(Uri(scheme: 'mailto', path: contactEmail)),
              ),
              ListTile(
                leading: const Icon(Icons.privacy_tip_outlined),
                title: Text(s.t('privacy')),
                onTap: () => launchUrl(Uri.parse(privacyUrl), mode: LaunchMode.inAppBrowserView),
              ),
              SwitchListTile(
                secondary: const Icon(Icons.dark_mode_outlined),
                title: Text(s.t('darkMode')),
                value: state.darkMode,
                onChanged: state.setDark,
              ),
            ],
          ),
        );
      },
    );
  }
}
