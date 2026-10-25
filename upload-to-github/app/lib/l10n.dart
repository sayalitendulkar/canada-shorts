/// All app text in English and French (Quebec requires full French).
/// Have a native French speaker review before launch.
class S {
  S(this.lang);
  final String lang;
  bool get fr => lang == 'fr';

  static Set<String> get enKeys => _en.keys.toSet();
  static Set<String> get frKeys => _fr.keys.toSet();

  static const _en = {
    'appName': 'Canada Shorts',
    'tagline': "Canada's news in 60 words",
    'langQ': 'Choose your language',
    'langSub': 'You can change this later in the menu.',
    'soon': 'Coming soon',
    'next': 'Continue',
    'provQ': 'Where do you live?',
    'provSub': 'We add local news from your province.',
    'skip': 'Skip',
    'topicsQ': 'What do you like to read?',
    'topicsSub': 'Pick at least 1. Change anytime from the menu.',
    'start': 'Start reading',
    'myFeed': 'My Feed',
    'allNews': 'All news',
    'saved': 'Saved stories',
    'feeds': 'FEEDS',
    'cats': 'CATEGORIES',
    'settings': 'SETTINGS',
    'menu': 'Menu',
    'language': 'Language',
    'province': 'Province',
    'editTopics': 'Edit my topics',
    'none': 'Not set',
    'about': 'About, contact and privacy',
    'aboutText': 'Canada Shorts summarises news from Canadian publishers in 60 words or fewer and links to the original story. Every card names its sources and shows which outlets covered it.',
    'contact': 'Contact us',
    'privacy': 'Privacy policy',
    'darkMode': 'Dark mode',
    'shortBy': 'short by Canada Shorts',
    'ai': 'AI summary',
    'editor': 'editor reviewed',
    'excerpt': 'publisher summary',
    'left': 'left',
    'centre': 'centre',
    'right': 'right',
    'official': 'official',
    'readMore': 'Read full story',
    'tapHere': 'Tap here',
    'end': "You're all caught up",
    'endSub': 'Pull down to check for new stories.',
    'empty': 'No stories here yet. Try another category from the menu.',
    'noSaved': 'Nothing saved yet. Tap the bookmark on any story.',
    'offline': "Can't reach the news right now. Showing saved news.",
    'noNews': "Can't load the news. Check your internet and pull down to try again.",
    'retry': 'Try again',
    'savedT': 'Saved',
    'unsavedT': 'Removed',
    'copied': 'Link copied',
    'report': 'Report this summary',
    'ad': 'Ad',
    'adNext': 'Swipe up for more news',
    'justNow': 'just now',
  };

  static const _fr = {
    'appName': 'Canada Shorts',
    'tagline': "L'actualité canadienne en 60 mots",
    'langQ': 'Choisissez votre langue',
    'langSub': 'Vous pourrez la changer dans le menu.',
    'soon': 'Bientôt',
    'next': 'Continuer',
    'provQ': 'Où habitez-vous?',
    'provSub': 'Nous ajoutons les nouvelles de votre province.',
    'skip': 'Passer',
    'topicsQ': "Qu'aimez-vous lire?",
    'topicsSub': 'Choisissez-en au moins 1. Modifiable dans le menu.',
    'start': 'Commencer la lecture',
    'myFeed': 'Mon fil',
    'allNews': 'Toutes les nouvelles',
    'saved': 'Articles enregistrés',
    'feeds': 'FILS',
    'cats': 'CATÉGORIES',
    'settings': 'PARAMÈTRES',
    'menu': 'Menu',
    'language': 'Langue',
    'province': 'Province',
    'editTopics': 'Modifier mes sujets',
    'none': 'Non défini',
    'about': 'À propos, contact et confidentialité',
    'aboutText': "Canada Shorts résume en 60 mots ou moins les nouvelles d'éditeurs canadiens et renvoie à l'article original. Chaque carte nomme ses sources et indique quels médias l'ont couverte.",
    'contact': 'Nous joindre',
    'privacy': 'Politique de confidentialité',
    'darkMode': 'Mode sombre',
    'shortBy': 'résumé par Canada Shorts',
    'ai': 'résumé par IA',
    'editor': 'révisé par un éditeur',
    'excerpt': "résumé de l'éditeur",
    'left': 'gauche',
    'centre': 'centre',
    'right': 'droite',
    'official': 'officiel',
    'readMore': "Lire l'article complet",
    'tapHere': 'Touchez ici',
    'end': 'Vous êtes à jour',
    'endSub': 'Glissez vers le bas pour voir les nouveautés.',
    'empty': 'Aucune nouvelle ici. Essayez une autre catégorie dans le menu.',
    'noSaved': "Rien d'enregistré. Touchez le signet sur une nouvelle.",
    'offline': 'Nouvelles inaccessibles pour le moment. Affichage des nouvelles enregistrées.',
    'noNews': 'Impossible de charger les nouvelles. Vérifiez votre connexion et glissez vers le bas.',
    'retry': 'Réessayer',
    'savedT': 'Enregistré',
    'unsavedT': 'Retiré',
    'copied': 'Lien copié',
    'report': 'Signaler ce résumé',
    'ad': 'Annonce',
    'adNext': 'Glissez vers le haut pour plus de nouvelles',
    'justNow': "à l'instant",
  };

  String t(String key) => (fr ? _fr : _en)[key] ?? _en[key] ?? key;

  String readAt(String source) => fr ? "Lire l'article complet sur $source" : 'Read the full story at $source';

  String covered(int n) => fr ? 'Couvert par $n média${n == 1 ? '' : 's'}' : 'Covered by $n outlet${n == 1 ? '' : 's'}';

  String updated(DateTime when) => fr ? 'Nouvelles mises à jour ${ago(when)}' : 'News updated ${ago(when)}';

  String ago(DateTime when) {
    final d = DateTime.now().difference(when);
    if (d.inMinutes < 1) return t('justNow');
    if (d.inHours < 1) return fr ? 'il y a ${d.inMinutes} min' : '${d.inMinutes} min ago';
    if (d.inDays < 1) return fr ? 'il y a ${d.inHours} h' : '${d.inHours}h ago';
    return fr ? 'il y a ${d.inDays} j' : '${d.inDays}d ago';
  }

  static const _topics = {
    'canada': ['Canada', 'Canada'],
    'politics': ['Politics', 'Politique'],
    'business': ['Business', 'Économie'],
    'money': ['Cost of Living', 'Coût de la vie'],
    'canada_us': ['Canada–U.S.', 'Canada–É.-U.'],
    'world': ['World', 'Monde'],
    'sports': ['Sports', 'Sports'],
    'tech': ['Tech & Science', 'Techno et science'],
    'climate': ['Climate', 'Climat'],
    'health': ['Health', 'Santé'],
    'indigenous': ['Indigenous', 'Autochtones'],
    'entertainment': ['Culture', 'Culture'],
  };

  String topic(String id) => _topics[id]?[fr ? 1 : 0] ?? id;

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

/// Languages offered at setup. Arabic, Hindi and Punjabi are shown as "coming soon".
class Lang {
  const Lang(this.id, this.name, this.ready);
  final String id;
  final String name;
  final bool ready;
}

const List<Lang> languages = [
  Lang('en', 'English', true),
  Lang('fr', 'Français', true),
  Lang('ar', 'العربية', false),
  Lang('hi', 'हिन्दी', false),
  Lang('pa', 'ਪੰਜਾਬੀ', false),
];
