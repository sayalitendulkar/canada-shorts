import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'screens/feed_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/api_client.dart';
import 'services/app_state.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final state = AppState();
  await state.load();
  runApp(CanadaShortsApp(state: state, api: ApiClient()));
}

class CanadaShortsApp extends StatelessWidget {
  const CanadaShortsApp({super.key, required this.state, required this.api});
  final AppState state;
  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    const red = Color(0xFFD52B1E); // maple-leaf red
    return ListenableBuilder(
      listenable: state,
      builder: (context, _) => MaterialApp(
        title: 'Canada Shorts',
        debugShowCheckedModeBanner: false,
        locale: Locale(state.lang),
        localizationsDelegates: GlobalMaterialLocalizations.delegates,
        supportedLocales: const [Locale('en', 'CA'), Locale('fr', 'CA'), Locale('en'), Locale('fr')],
        themeMode: state.darkMode ? ThemeMode.dark : ThemeMode.light,
        theme: ThemeData(colorSchemeSeed: red, useMaterial3: true),
        darkTheme: ThemeData(colorSchemeSeed: red, brightness: Brightness.dark, useMaterial3: true),
        home: state.onboarded ? FeedScreen(state: state, api: api) : OnboardingScreen(state: state),
      ),
    );
  }
}
