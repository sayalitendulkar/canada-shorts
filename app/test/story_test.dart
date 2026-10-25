import 'package:canada_shorts/l10n.dart';
import 'package:canada_shorts/models/story.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Story parses API JSON and round-trips for the offline cache', () {
    final json = {
      'id': 7,
      'lang': 'fr',
      'headline': 'La Banque du Canada abaisse son taux',
      'summary': 'La Banque du Canada a abaissé son taux directeur à 2,25 %.',
      'summary_by': 'editor',
      'category': 'business',
      'image_url': null,
      'lead_source': 'La Presse',
      'read_more_url': 'https://lapresse.ca/d1',
      'published_at': '2026-10-24T12:00:00+00:00',
      'sources': [
        {'name': 'La Presse', 'url': 'https://lapresse.ca/d1', 'bias': 'lean_left'}
      ],
      'bias': {'left': 1, 'centre': 0, 'right': 0, 'official': 0, 'total': 1, 'blindspot': null},
    };
    final s = Story.fromJson(json);
    expect(s.bias.left, 1);
    expect(Story.fromJson(s.toJson()).headline, s.headline);
  });

  test('French strings exist for every English key', () {
    expect(S.frKeys, S.enKeys);
    expect(S('fr').t('readMore'), "Lire l'article complet");
    expect(S('fr').provinceName('QC'), 'Québec');
  });
}
