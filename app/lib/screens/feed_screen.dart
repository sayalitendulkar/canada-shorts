import 'package:flutter/material.dart';

import '../l10n.dart';
import '../models/story.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';
import '../widgets/story_card.dart';
import 'bookmarks_screen.dart';
import 'settings_screen.dart';

class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key, required this.state, required this.api});
  final AppState state;
  final ApiClient api;

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  final _pages = PageController();
  List<Category> _categories = [];
  String _category = 'top';
  List<Story> _stories = [];
  bool _loading = true;
  bool _offline = false;
  late String _lang;
  String? _province;

  AppState get st => widget.state;

  @override
  void initState() {
    super.initState();
    _lang = st.lang;
    _province = st.province;
    st.addListener(_onSettings);
    _load();
  }

  @override
  void dispose() {
    st.removeListener(_onSettings);
    _pages.dispose();
    super.dispose();
  }

  void _onSettings() {
    if (st.lang != _lang || st.province != _province) {
      _lang = st.lang;
      _province = st.province;
      _categories = [];
      if (_province == null && _category == 'province') _category = 'top';
      _load();
    } else {
      setState(() {}); // e.g. bookmark icon changed
    }
  }

  String get _cacheKey => '${st.lang}_$_category';

  Future<void> _load() async {
    if (mounted) setState(() => _loading = true);
    try {
      if (_categories.isEmpty) {
        final cats = await widget.api.categories(st.lang);
        // "My Province" only makes sense once a province is chosen.
        _categories = cats.where((c) => c.id != 'province' || st.province != null).toList();
      }
      final stories = await widget.api.feed(
        lang: st.lang,
        category: _category,
        province: st.province,
      );
      await st.cacheFeed(_cacheKey, stories);
      _stories = stories;
      _offline = false;
    } catch (_) {
      _stories = st.cachedFeed(_cacheKey);
      _offline = true;
    }
    if (!mounted) return;
    setState(() => _loading = false);
    if (_pages.hasClients) _pages.jumpToPage(0);
  }

  void _pick(String id) {
    if (id == _category) return;
    _category = id;
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final s = st.s;
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('appName'), style: const TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            tooltip: s.t('bookmarks'),
            icon: const Icon(Icons.bookmarks_outlined),
            onPressed: () => Navigator.push(context,
                MaterialPageRoute(builder: (_) => BookmarksScreen(state: st, api: widget.api))),
          ),
          IconButton(
            tooltip: s.t('settings'),
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SettingsScreen(state: st))),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                for (final c in _categories)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(c.id == 'province' && st.province != null ? s.provinceName(st.province!) : c.label),
                      selected: c.id == _category,
                      onSelected: (_) => _pick(c.id),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
      body: Column(
        children: [
          if (_offline)
            MaterialBanner(
              content: Text(s.t('offline')),
              actions: [TextButton(onPressed: _load, child: Text(s.t('retry')))],
            ),
          Expanded(child: _body(s)),
        ],
      ),
    );
  }

  Widget _body(S s) {
    if (_loading && _stories.isEmpty) return const Center(child: CircularProgressIndicator());
    return RefreshIndicator(
      onRefresh: _load,
      child: _stories.isEmpty
          ? ListView(children: [Padding(padding: const EdgeInsets.all(32), child: Text(s.t('empty')))])
          : PageView.builder(
              controller: _pages,
              scrollDirection: Axis.vertical,
              itemCount: _stories.length + 1,
              itemBuilder: (context, i) => i == _stories.length
                  ? Center(child: Text(s.t('allCaughtUp'), style: Theme.of(context).textTheme.titleMedium))
                  : StoryCard(story: _stories[i], state: st, api: widget.api),
            ),
    );
  }
}
