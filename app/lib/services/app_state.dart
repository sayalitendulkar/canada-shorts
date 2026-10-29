import 'dart:convert';
import 'dart:ui' show PlatformDispatcher;

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../l10n.dart';
import '../models/story.dart';

/// Reader choices and saved stories. Stored only on the phone: no account,
/// no location tracking.
class AppState extends ChangeNotifier {
  late SharedPreferences _p;

  String lang = 'en';
  String? province;
  List<String> topics = [];
  bool darkMode = false;
  bool onboarded = false;
  final List<Story> bookmarks = [];
  final Map<String, String> reactions = {}; // "lang:id" -> reaction id (this phone only for now)

  S get s => S(lang);

  Future<void> load() async {
    _p = await SharedPreferences.getInstance();
    final deviceFr = PlatformDispatcher.instance.locale.languageCode == 'fr';
    lang = _p.getString('lang') ?? (deviceFr ? 'fr' : 'en');
    province = _p.getString('province');
    topics = _p.getStringList('topics') ?? [];
    darkMode = _p.getBool('dark') ?? false;
    onboarded = (_p.getBool('onboarded') ?? false) && topics.isNotEmpty;
    bookmarks
      ..clear()
      ..addAll(_decode(_p.getString('bookmarks')));
    reactions.clear();
    try {
      final raw = _p.getString('reactions');
      if (raw != null) reactions.addAll(Map<String, String>.from(jsonDecode(raw) as Map));
    } catch (_) {}
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

  Future<void> setTopics(List<String> v) async {
    topics = List.of(v);
    await _p.setStringList('topics', topics);
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

  String? reactionFor(Story st) => reactions['${st.lang}:${st.id}'];

  /// Pick a reaction; picking the same one again removes it.
  Future<void> react(Story st, String reaction) async {
    final key = '${st.lang}:${st.id}';
    if (reactions[key] == reaction) {
      reactions.remove(key);
    } else {
      reactions[key] = reaction;
    }
    // Keep only the newest 500 so the phone's storage stays small.
    while (reactions.length > 500) {
      reactions.remove(reactions.keys.first);
    }
    await _p.setString('reactions', jsonEncode(reactions));
    notifyListeners();
  }

  bool isSaved(Story st) => bookmarks.any((b) => b.id == st.id && b.lang == st.lang);

  Future<bool> toggleBookmark(Story st) async {
    final was = isSaved(st);
    if (was) {
      bookmarks.removeWhere((b) => b.id == st.id && b.lang == st.lang);
    } else {
      bookmarks.insert(0, st);
    }
    await _p.setString('bookmarks', jsonEncode(bookmarks.map((b) => b.toJson()).toList()));
    notifyListeners();
    return !was;
  }
}
