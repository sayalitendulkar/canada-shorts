/// All UI text in English and French. French must be complete (Quebec Charter
/// of the French Language); have a native speaker review before launch.
class S {
  S(this.lang);
  final String lang;
  bool get fr => lang == 'fr';

  static Set<String> get enKeys => _en.keys.toSet();
  static Set<String> get frKeys => _fr.keys.toSet();

  static const _en = {
    'appName': 'Canada Shorts',
    'welcome': 'Canada\'s news in 60 words',
    'chooseLang': 'Choose your language',
    'chooseProvince': 'Where do you live?',
    'provinceHint': 'We use this to show local stories. You can change it any time.',
    'skip': 'Skip',
    'start': 'Start reading',
    'readMore': 'Read full story',
    'sources': 'sources',
    'source': 'source',
    'left': 'Left',
    'centre': 'Centre',
    'right': 'Right',
    'official': 'Official',
    'blindLeft': 'Covered mostly by left-leaning outlets',
    'blindRight': 'Covered mostly by right-leaning outlets',
    'aiLabel': 'Summary by AI from publisher feeds',
    'editorLabel': 'Summary reviewed by an editor',
    'excerptLabel': 'Excerpt from the publisher',
    'report': 'Report this summary',
    'reportHint': 'What\'s wrong? (e.g. a wrong fact, biased wording)',
    'send': 'Send',
    'cancel': 'Cancel',
    'thanks': 'Thanks — an editor will check it.',
    'saved': 'Saved',
    'bookmarks': 'Saved stories',
    'noBookmarks': 'Nothing saved yet. Tap the bookmark on any card.',
    'settings': 'Settings',
    'language': 'Language',
    'province': 'Province or territory',
    'none': 'Not set',
    'darkMode': 'Dark mode',
    'about': 'About and contact',
    'aboutText': 'Canada Shorts summarises news from Canadian publishers in 60 words or fewer and links to the original story. Every card names its sources and shows which outlets covered it.',
    'contact': 'Contact us',
    'privacy': 'Privacy policy',
    'offline': 'Can\'t reach the news server. Showing saved cards.',
    'empty': 'No stories here yet. Pull down to refresh.',
    'retry': 'Retry',
    'allCaughtUp': 'You\'re all caught up',
    'ago_m': 'm ago',
    'ago_h': 'h ago',
    'ago_d': 'd ago',
    'justNow': 'just now',
  };

  static const _fr = {
    'appName': 'Canada Shorts',
    'welcome': 'L\'actualité canadienne en 60 mots',
    'chooseLang': 'Choisissez votre langue',
    'chooseProvince': 'Où habitez-vous?',
    'provinceHint': 'Nous l\'utilisons pour afficher les nouvelles locales. Vous pouvez le changer en tout temps.',
    'skip': 'Passer',
    'start': 'Commencer la lecture',
    'readMore': 'Lire l\'article complet',
    'sources': 'sources',
    'source': 'source',
    'left': 'Gauche',
    'centre': 'Centre',
    'right': 'Droite',
    'official': 'Officiel',
    'blindLeft': 'Couvert surtout par des médias de gauche',
    'blindRight': 'Couvert surtout par des médias de droite',
    'aiLabel': 'Résumé par IA à partir des fils des éditeurs',
    'editorLabel': 'Résumé révisé par un éditeur',
    'excerptLabel': 'Extrait de l\'éditeur',
    'report': 'Signaler ce résumé',
    'reportHint': 'Quel est le problème? (ex. fait erroné, formulation biaisée)',
    'send': 'Envoyer',
    'cancel': 'Annuler',
    'thanks': 'Merci — un éditeur va vérifier.',
    'saved': 'Enregistré',
    'bookmarks': 'Articles enregistrés',
    'noBookmarks': 'Rien d\'enregistré. Touchez le signet sur une carte.',
    'settings': 'Paramètres',
    'language': 'Langue',
    'province': 'Province ou territoire',
    'none': 'Non défini',
    'darkMode': 'Mode sombre',
    'about': 'À propos et contact',
    'aboutText': 'Canada Shorts résume en 60 mots ou moins les nouvelles d\'éditeurs canadiens et renvoie à l\'article original. Chaque carte nomme ses sources et indique quels médias l\'ont couverte.',
    'contact': 'Nous joindre',
    'privacy': 'Politique de confidentialité',
    'offline': 'Serveur injoignable. Affichage des cartes enregistrées.',
    'empty': 'Aucune nouvelle ici pour l\'instant. Glissez vers le bas pour actualiser.',
    'retry': 'Réessayer',
    'allCaughtUp': 'Vous êtes à jour',
    'ago_m': 'min',
    'ago_h': 'h',
    'ago_d': 'j',
    'justNow': 'à l\'instant',
  };

  String t(String key) => (fr ? _fr : _en)[key] ?? key;

  String ago(DateTime when) {
    final d = DateTime.now().difference(when);
    String fmt(int n, String unit) => fr ? 'il y a $n ${t(unit)}' : '$n${t(unit)}';
    if (d.inMinutes < 1) return t('justNow');
    if (d.inHours < 1) return fmt(d.inMinutes, 'ago_m');
    if (d.inDays < 1) return fmt(d.inHours, 'ago_h');
    return fmt(d.inDays, 'ago_d');
  }

  static const provinceNames = {
    'ON': ['Ontario', 'Ontario'],
    'QC': ['Quebec', 'Québec'],
    'BC': ['British Columbia', 'Colombie-Britannique'],
    'AB': ['Alberta', 'Alberta'],
    'MB': ['Manitoba', 'Manitoba'],
    'SK': ['Saskatchewan', 'Saskatchewan'],
    'NS': ['Nova Scotia', 'Nouvelle-Écosse'],
    'NB': ['New Brunswick', 'Nouveau-Brunswick'],
    'NL': ['Newfoundland and Labrador', 'Terre-Neuve-et-Labrador'],
    'PE': ['Prince Edward Island', 'Île-du-Prince-Édouard'],
    'YT': ['Yukon', 'Yukon'],
    'NT': ['Northwest Territories', 'Territoires du Nord-Ouest'],
    'NU': ['Nunavut', 'Nunavut'],
  };

  String provinceName(String code) => provinceNames[code]?[fr ? 1 : 0] ?? code;
}
