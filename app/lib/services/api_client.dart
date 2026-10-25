import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';
import '../models/story.dart';

/// Downloads the ready-made news files from the GitHub website and keeps the
/// last copy on the phone so the app works offline.
class NewsService {
  NewsService({http.Client? client}) : _http = client ?? http.Client();
  final http.Client _http;

  Feed _parse(String body, {bool fromCache = false}) {
    final data = jsonDecode(body) as Map<String, dynamic>;
    final stories = ((data['stories'] ?? const []) as List)
        .map((e) => Story.fromJson(e as Map<String, dynamic>))
        .toList();
    return Feed(
      stories: stories,
      generatedAt: DateTime.tryParse((data['generated_at'] ?? '') as String)?.toLocal(),
      fromCache: fromCache,
    );
  }

  /// Last downloaded copy, if any (shown instantly while the new one loads).
  Future<Feed?> cached(String lang) async {
    final p = await SharedPreferences.getInstance();
    final raw = p.getString('feed_$lang');
    if (raw == null) return null;
    try {
      return _parse(raw, fromCache: true);
    } catch (_) {
      return null;
    }
  }

  /// Fresh copy from the internet. Throws if offline.
  Future<Feed> fetch(String lang) async {
    final uri = Uri.parse('${feedBase}data/feed_$lang.json')
        .replace(queryParameters: {'t': '${DateTime.now().millisecondsSinceEpoch ~/ 60000}'});
    final r = await _http.get(uri).timeout(const Duration(seconds: 15));
    if (r.statusCode != 200) throw Exception('news ${r.statusCode}');
    final body = utf8.decode(r.bodyBytes);
    final feed = _parse(body);
    final p = await SharedPreferences.getInstance();
    await p.setString('feed_$lang', body);
    return feed;
  }

  /// Same rules as the web preview: My Feed = chosen topics + your province.
  static List<Story> filter(List<Story> all, {required String view, required List<String> topics, String? province}) {
    bool inProv(Story s) => province != null && s.provinces.contains(province);
    List<Story> list;
    switch (view) {
      case 'myfeed':
        list = all.where((s) => topics.contains(s.category) || inProv(s)).toList();
        break;
      case 'top':
        list = List.of(all);
        break;
      case 'province':
        list = all.where(inProv).toList();
        break;
      default:
        list = all.where((s) => s.category == view).toList();
    }
    if (province != null) {
      double boosted(Story s) => s.rank * (inProv(s) ? 1.4 : 1.0); // local news gets a boost
      list.sort((a, b) => boosted(b).compareTo(boosted(a)));
    }
    return list.take(80).toList();
  }
}
