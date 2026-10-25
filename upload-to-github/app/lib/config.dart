/// Where the news comes from: the free GitHub website that the news program
/// refreshes every 30 minutes. Change it if you move the news files.
const String feedBase = String.fromEnvironment(
  'FEED_BASE',
  defaultValue: 'https://sayalitendulkar.github.io/canada-shorts/',
);

/// Google Play requires a real contact address inside news apps.
const String contactEmail = String.fromEnvironment('CONTACT_EMAIL', defaultValue: 'your-email@example.com');
const String privacyUrl = '${feedBase}privacy.html';

/// AdMob. These defaults are Google's official TEST ad units: safe to tap,
/// earn nothing. Replace with your own IDs (from admob.google.com) at launch.
const String bannerAdUnitId = String.fromEnvironment(
  'ADMOB_BANNER',
  defaultValue: 'ca-app-pub-3940256099942544/6300978111',
);

/// Show one ad card after this many stories.
const int adEvery = 10;

const List<String> provinceCodes = [
  'ON', 'QC', 'BC', 'AB', 'MB', 'SK', 'NS', 'NB', 'NL', 'PE', 'YT', 'NT', 'NU'
];

/// Topic ids, same as the news program (backend/app/categorize.py).
const List<String> topicIds = [
  'canada', 'politics', 'business', 'money', 'canada_us', 'world', 'sports',
  'tech', 'climate', 'health', 'indigenous', 'entertainment',
];
