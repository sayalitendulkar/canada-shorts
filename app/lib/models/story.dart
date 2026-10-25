class SourceRef {
  SourceRef({required this.name, required this.url, required this.bias});
  final String name;
  final String url;
  final String bias;

  factory SourceRef.fromJson(Map<String, dynamic> j) => SourceRef(
        name: (j['name'] ?? '') as String,
        url: (j['url'] ?? '') as String,
        bias: (j['bias'] ?? 'centre') as String,
      );

  Map<String, dynamic> toJson() => {'name': name, 'url': url, 'bias': bias};
}

class BiasMix {
  BiasMix({this.left = 0, this.centre = 0, this.right = 0, this.official = 0, this.total = 0, this.blindspot});
  final int left, centre, right, official, total;
  final String? blindspot;

  static int _i(dynamic v) => v is num ? v.toInt() : 0;

  factory BiasMix.fromJson(Map<String, dynamic> j) => BiasMix(
        left: _i(j['left']),
        centre: _i(j['centre']),
        right: _i(j['right']),
        official: _i(j['official']),
        total: _i(j['total']),
        blindspot: j['blindspot'] as String?,
      );

  Map<String, dynamic> toJson() =>
      {'left': left, 'centre': centre, 'right': right, 'official': official, 'total': total, 'blindspot': blindspot};
}

class Story {
  Story({
    required this.id,
    required this.lang,
    required this.headline,
    required this.summary,
    required this.summaryBy,
    required this.category,
    required this.provinces,
    required this.imageUrl,
    required this.leadSource,
    required this.readMoreUrl,
    required this.publishedAt,
    required this.sources,
    required this.bias,
    required this.rank,
  });

  final int id;
  final String lang;
  final String headline;
  final String summary;
  final String summaryBy; // ai | editor | excerpt
  final String category;
  final List<String> provinces;
  final String? imageUrl;
  final String leadSource;
  final String readMoreUrl;
  final DateTime publishedAt;
  final List<SourceRef> sources;
  final BiasMix bias;
  final double rank;

  factory Story.fromJson(Map<String, dynamic> j) => Story(
        id: (j['id'] as num).toInt(),
        lang: (j['lang'] ?? 'en') as String,
        headline: (j['headline'] ?? '') as String,
        summary: (j['summary'] ?? '') as String,
        summaryBy: (j['summary_by'] ?? 'excerpt') as String,
        category: (j['category'] ?? 'canada') as String,
        provinces: ((j['provinces'] ?? const []) as List).map((e) => e.toString()).toList(),
        imageUrl: j['image_url'] as String?,
        leadSource: (j['lead_source'] ?? '') as String,
        readMoreUrl: (j['read_more_url'] ?? '') as String,
        publishedAt: DateTime.tryParse((j['published_at'] ?? '') as String)?.toLocal() ?? DateTime.now(),
        sources: ((j['sources'] ?? const []) as List).map((e) => SourceRef.fromJson(e as Map<String, dynamic>)).toList(),
        bias: BiasMix.fromJson((j['bias'] ?? const <String, dynamic>{}) as Map<String, dynamic>),
        rank: j['rank'] is num ? (j['rank'] as num).toDouble() : 0.0,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'lang': lang,
        'headline': headline,
        'summary': summary,
        'summary_by': summaryBy,
        'category': category,
        'provinces': provinces,
        'image_url': imageUrl,
        'lead_source': leadSource,
        'read_more_url': readMoreUrl,
        'published_at': publishedAt.toUtc().toIso8601String(),
        'sources': sources.map((s) => s.toJson()).toList(),
        'bias': bias.toJson(),
        'rank': rank,
      };
}

/// One download of the news file.
class Feed {
  Feed({required this.stories, required this.generatedAt, this.fromCache = false});
  final List<Story> stories;
  final DateTime? generatedAt;
  final bool fromCache;
}
