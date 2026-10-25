import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'screens/feed_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/api_client.dart';
import 'services/app_state.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  unawaited(MobileAds.instance.initialize());
  final state = AppState();
  await state.load();
  runApp(CanadaShortsApp(state: state, news: NewsService()));
}

class CanadaShortsApp extends StatelessWidget {
  const CanadaShortsApp({super.key, required this.state, required this.news});
  final AppState state;
  final NewsService news;

  static const red = Color(0xFFE8412C);

  @override
  Widget build(BuildContext context) {
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
        home: state.onboarded
            ? FeedScreen(state: state, news: news)
            : OnboardingScreen(state: state),
      ),
    );
  }
}
