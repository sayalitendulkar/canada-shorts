import 'package:canada_shorts/l10n.dart';
import 'package:canada_shorts/models/story.dart';
import 'package:canada_shorts/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

Story _story(int id, String cat, {List<String> prov = const [], double rank = 1}) => Story.fromJson({
      'id': id,
      'lang': 'en',
      'headline': 'H$id',
      'summary': 'S$id',
      'summary_by': 'ai',
      'category': cat,
      'provinces': prov,
      'image_url': null,
      'lead_source': 'CBC News',
      'read_more_url': 'https://cbc.ca/$id',
      'published_at': '2026-10-24T12:00:00+00:00',
      'sources': [
        {'name': 'CBC News', 'url': 'https://cbc.ca/$id', 'bias': 'lean_left'}
      ],
      'bias': {'left': 1, 'centre': 0, 'right': 0, 'official': 0, 'total': 1, 'blindspot': null},
      'rank': rank,
    });

void main() {
  test('Story parses the news file and round-trips for saved stories', () {
    final s = _story(7, 'business', prov: ['ON']);
    expect(s.bias.left, 1);
    expect(s.provinces, ['ON']);
    final again = Story.fromJson(s.toJson());
    expect(again.headline, s.headline);
    expect(again.rank, s.rank);
  });

  test('My Feed shows chosen topics plus local news, local first', () {
    final all = [
      _story(1, 'sports', rank: 3),
      _story(2, 'politics', rank: 2),
      _story(3, 'climate', prov: ['BC'], rank: 1.9),
      _story(4, 'world', rank: 5),
    ];
    final mine = NewsService.filter(all, view: 'myfeed', topics: ['sports', 'politics'], province: 'BC');
    expect(mine.map((s) => s.id).toList(), [1, 3, 2]); // 1.9 x 1.4 = 2.66 puts BC ahead of politics
    final sports = NewsService.filter(all, view: 'sports', topics: const [], province: null);
    expect(sports.map((s) => s.id).toList(), [1]);
  });

  test('French text exists for every English key', () {
    expect(S.frKeys, S.enKeys);
    expect(S('fr').t('readMore'), "Lire l'article complet");
    expect(S('fr').provinceName('QC'), 'Québec');
    expect(S('fr').topic('money'), 'Coût de la vie');
  });
}
