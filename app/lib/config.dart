/// Backend address. 10.0.2.2 is your computer as seen from the Android emulator.
/// Override at build time: flutter run --dart-define=API_BASE=https://api.example.ca
const String apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8000');

/// Shown on the About screen (Google Play news policy needs an in-app contact).
const String contactEmail = 'hello@example.ca';
const String privacyUrl = 'https://example.ca/privacy';

const List<String> provinceCodes = [
  'ON', 'QC', 'BC', 'AB', 'MB', 'SK', 'NS', 'NB', 'NL', 'PE', 'YT', 'NT', 'NU'
];
