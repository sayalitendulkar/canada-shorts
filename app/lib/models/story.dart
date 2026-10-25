class SourceRef {
  SourceRef({required this.name, required this.url, required this.bias});
  final String name;
  final String url;
  final String bias;

  factory SourceRef.fromJson(Map<String, dynamic> j) =>
      SourceRef(name: j['name'] as String, url: j['url'] as String, bias: j['bias'] as String);

  Map<String, dynamic> toJson() => {'name': name, 'url': url, 'bias': bias};
}

class BiasMix {
  BiasMix({this.left = 0, this.centre = 0, this.right = 0, this.official = 0, this.total = 0, this.blindspot});
  final int left, centre, right, official, total;
  final String? blindspot;

  factory BiasMix.fromJson(Map<String, dynamic> j) => BiasMix(
        left: j['left'] ?? 0,
        centre: j['centre'] ?? 0,
        right: j['right'] ?? 0,
        official: j['official'] ?? 0,
        total: j['total'] ?? 0,
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
    required this.imageUrl,
    required this.leadSource,
    required this.readMoreUrl,
    required this.publishedAt,
    required this.sources,
    required this.bias,
  });

  final int id;
  final String lang;
  final String headline;
  final String summary;
  final String summaryBy; // ai | editor | excerpt
  final String category;
  final String? imageUrl;
  final String leadSource;
  final String readMoreUrl;
  final DateTime publishedAt;
  final List<SourceRef> sources;
  final BiasMix bias;

  factory Story.fromJson(Map<String, dynamic> j) => Story(
        id: j['id'] as int,
        lang: j['lang'] as String,
        headline: (j['headline'] ?? '') as String,
        summary: (j['summary'] ?? '') as String,
        summaryBy: (j['summary_by'] ?? 'excerpt') as String,
        category: (j['category'] ?? 'canada') as String,
        imageUrl: j['image_url'] as String?,
        leadSource: (j['lead_source'] ?? '') as String,
        readMoreUrl: (j['read_more_url'] ?? '') as String,
        publishedAt: DateTime.tryParse(j['published_at'] as String? ?? '')?.toLocal() ?? DateTime.now(),
        sources: ((j['sources'] ?? []) as List).map((e) => SourceRef.fromJson(e as Map<String, dynamic>)).toList(),
        bias: BiasMix.fromJson((j['bias'] ?? {}) as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'lang': lang,
        'headline': headline,
        'summary': summary,
        'summary_by': summaryBy,
        'category': category,
        'image_url': imageUrl,
        'lead_source': leadSource,
        'read_more_url': readMoreUrl,
        'published_at': publishedAt.toUtc().toIso8601String(),
        'sources': sources.map((s) => s.toJson()).toList(),
        'bias': bias.toJson(),
      };
}

class Category {
  Category(this.id, this.label);
  final String id;
  final String label;
}
