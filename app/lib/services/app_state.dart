import 'dart:convert';
import 'dart:ui' show PlatformDispatcher;

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../l10n.dart';
import '../models/story.dart';

/// Reader settings, bookmarks and the offline cache. Stored only on the
/// device: no account, no location tracking (privacy by default, Law 25).
class AppState extends ChangeNotifier {
  late SharedPreferences _p;

  String lang = 'en';
  String? province;
  bool darkMode = false;
  bool onboarded = false;
  final List<Story> bookmarks = [];

  S get s => S(lang);

  Future<void> load() async {
    _p = await SharedPreferences.getInstance();
    final deviceFr = PlatformDispatcher.instance.locale.languageCode == 'fr';
    lang = _p.getString('lang') ?? (deviceFr ? 'fr' : 'en');
    province = _p.getString('province');
    darkMode = _p.getBool('dark') ?? false;
    onboarded = _p.getBool('onboarded') ?? false;
    bookmarks
      ..clear()
      ..addAll(_decode(_p.getString('bookmarks')));
  }

  List<Story> _decode(String? raw) {
    if (raw == null) return [];
    try {
      return (jsonDecode(raw) as List).map((e) => Story.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> setLang(String v) async {
    lang = v;
    await _p.setString('lang', v);
    notifyListeners();
  }

  Future<void> setProvince(String? v) async {
    province = v;
    if (v == null) {
      await _p.remove('province');
    } else {
      await _p.setString('province', v);
    }
    notifyListeners();
  }

  Future<void> setDark(bool v) async {
    darkMode = v;
    await _p.setBool('dark', v);
    notifyListeners();
  }

  Future<void> finishOnboarding() async {
    onboarded = true;
    await _p.setBool('onboarded', true);
    notifyListeners();
  }

  bool isSaved(Story st) => bookmarks.any((b) => b.id == st.id);

  Future<void> toggleBookmark(Story st) async {
    if (isSaved(st)) {
      bookmarks.removeWhere((b) => b.id == st.id);
    } else {
      bookmarks.insert(0, st);
    }
    await _p.setString('bookmarks', jsonEncode(bookmarks.map((b) => b.toJson()).toList()));
    notifyListeners();
  }

  // Offline cache: the last 100 cards per language + category.
  Future<void> cacheFeed(String key, List<Story> stories) =>
      _p.setString('cache_$key', jsonEncode(stories.take(100).map((x) => x.toJson()).toList()));

  List<Story> cachedFeed(String key) => _decode(_p.getString('cache_$key'));
}
