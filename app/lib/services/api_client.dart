import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../models/story.dart';

class ApiClient {
  ApiClient({http.Client? client}) : _http = client ?? http.Client();
  final http.Client _http;

  Uri _u(String path, [Map<String, String>? q]) => Uri.parse('$apiBase$path').replace(queryParameters: q);

  Future<List<Story>> feed({required String lang, String? category, String? province, int limit = 40}) async {
    final q = <String, String>{'lang': lang, 'limit': '$limit'};
    if (category != null) q['category'] = category;
    if (province != null) q['province'] = province;
    final r = await _http.get(_u('/feed', q)).timeout(const Duration(seconds: 12));
    if (r.statusCode != 200) throw Exception('feed ${r.statusCode}');
    final data = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    return (data['stories'] as List).map((e) => Story.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Category>> categories(String lang) async {
    final r = await _http.get(_u('/categories', {'lang': lang})).timeout(const Duration(seconds: 8));
    if (r.statusCode != 200) throw Exception('categories ${r.statusCode}');
    final list = jsonDecode(utf8.decode(r.bodyBytes)) as List;
    return list.map((e) => Category(e['id'] as String, e['label'] as String)).toList();
  }

  Future<void> report(int storyId, String reason) async {
    final r = await _http.post(
      _u('/report'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'story_id': storyId, 'reason': reason}),
    );
    if (r.statusCode != 201) throw Exception('report ${r.statusCode}');
  }
}
