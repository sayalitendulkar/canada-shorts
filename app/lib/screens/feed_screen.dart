import 'package:flutter/material.dart';

import '../config.dart';
import '../models/story.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';
import '../widgets/ad_card.dart';
import '../widgets/story_card.dart';
import 'onboarding_screen.dart';
import 'settings_screen.dart';

/// The main screen: one story per swipe, a menu on the right side.
class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key, required this.state, required this.news});
  final AppState state;
  final NewsService news;

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> with WidgetsBindingObserver {
  static const red = Color(0xFFE8412C);
  final _pages = PageController();
  final _scaffold = GlobalKey<ScaffoldState>();

  String view = 'myfeed'; // myfeed | top | province | saved | a topic id
  Feed? feed;
  bool loading = true;
  bool failed = false;
  DateTime lastLoad = DateTime.fromMillisecondsSinceEpoch(0);
  late String _lang;

  AppState get st => widget.state;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _lang = st.lang;
    st.addListener(_onSettings);
    _load(showCachedFirst: true);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    st.removeListener(_onSettings);
    _pages.dispose();
    super.dispose();
  }

  // Coming back to the app after 15+ minutes: get fresh news.
  @override
  void didChangeAppLifecycleState(AppLifecycleState s) {
    if (s == AppLifecycleState.resumed && DateTime.now().difference(lastLoad).inMinutes >= 15) {
      _load();
    }
  }

  void _onSettings() {
    if (st.lang != _lang) {
      _lang = st.lang;
      feed = null;
      _load(showCachedFirst: true);
    } else {
      if (view == 'province' && st.province == null) view = 'myfeed';
      if (mounted) setState(() {});
    }
  }

  Future<void> _load({bool showCachedFirst = false}) async {
    final lang = st.lang;
    if (showCachedFirst && feed == null) {
      final c = await widget.news.cached(lang);
      if (c != null && mounted && lang == st.lang) setState(() => feed = c);
    }
    if (mounted) setState(() => loading = true);
    try {
      final f = await widget.news.fetch(lang);
      if (!mounted || lang != st.lang) return;
      setState(() {
        feed = f;
        failed = false;
        lastLoad = DateTime.now();
      });
    } catch (_) {
      if (mounted) setState(() => failed = true);
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  void _go(String v) {
    Navigator.of(context).pop(); // close the menu
    setState(() => view = v);
    if (_pages.hasClients) _pages.jumpToPage(0);
  }

  String _title() {
    final s = st.s;
    switch (view) {
      case 'myfeed':
        return s.t('myFeed');
      case 'top':
        return s.t('allNews');
      case 'saved':
        return s.t('saved');
      case 'province':
        return st.province == null ? s.t('province') : s.provinceName(st.province!);
      default:
        return s.topic(view);
    }
  }

  List<Story> _stories() {
    if (view == 'saved') return st.bookmarks.where((b) => b.lang == st.lang).toList();
    final all = feed?.stories ?? const <Story>[];
    return NewsService.filter(all, view: view, topics: st.topics, province: st.province);
  }

  @override
  Widget build(BuildContext context) {
    final s = st.s;
    final stories = _stories();
    // Mix in one ad card after every [adEvery] stories (not in Saved).
    final items = <Object>[];
    for (var i = 0; i < stories.length; i++) {
      items.add(stories[i]);
      if (view != 'saved' && (i + 1) % adEvery == 0 && i + 1 < stories.length) items.add('ad');
    }

    Widget body;
    if (stories.isEmpty) {
      final msg = loading && feed == null
          ? null
          : (view == 'saved' ? s.t('noSaved') : (failed && feed == null ? s.t('noNews') : s.t('empty')));
      body = RefreshIndicator(
        onRefresh: _load,
        child: ListView(children: [
          SizedBox(
            height: 400,
            child: Center(
              child: msg == null
                  ? const CircularProgressIndicator()
                  : Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text(msg, textAlign: TextAlign.center, style: const TextStyle(fontSize: 15)),
                    ),
            ),
          ),
        ]),
      );
    } else {
      body = RefreshIndicator(
        onRefresh: _load,
        child: PageView.builder(
          controller: _pages,
          scrollDirection: Axis.vertical,
          itemCount: items.length + 1,
          itemBuilder: (context, i) {
            if (i == items.length) return _endCard();
            final item = items[i];
            if (item is Story) return StoryCard(story: item, state: st);
            return AdCard(s: s);
          },
        ),
      );
    }

    return Scaffold(
      key: _scaffold,
      appBar: AppBar(
        backgroundColor: const Color(0xFF111111),
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false,
        titleSpacing: 18,
        title: Row(children: [
          const Text('CS', style: TextStyle(color: red, fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(width: 8),
          Flexible(
            child: Text(_title(),
                overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          ),
        ]),
        actions: [
          IconButton(
            icon: const Icon(Icons.menu),
            tooltip: s.t('menu'),
            onPressed: () => _scaffold.currentState?.openEndDrawer(),
          ),
        ],
      ),
      endDrawer: _menu(),
      body: Column(children: [
        if (failed && feed != null && feed!.fromCache)
          MaterialBanner(
            content: Text(s.t('offline')),
            actions: [TextButton(onPressed: _load, child: Text(s.t('retry')))],
          ),
        Expanded(child: body),
      ]),
    );
  }

  Widget _endCard() {
    final s = st.s;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(s.t('end'), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(s.t('endSub'), textAlign: TextAlign.center),
        ]),
      ),
    );
  }

  Widget _menu() {
    final s = st.s;
    Widget header(String text) => Padding(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 6),
          child: Text(text,
              style: const TextStyle(fontSize: 12, letterSpacing: 0.8, fontWeight: FontWeight.w600, color: Colors.grey)),
        );
    Widget item(String label, String? v, {String? trailing, VoidCallback? onTap}) {
      final on = v != null && v == view;
      return ListTile(
        dense: true,
        title: Text(label,
            style: TextStyle(
                fontSize: 15, color: on ? red : null, fontWeight: on ? FontWeight.w600 : FontWeight.w400)),
        trailing: trailing == null ? (on ? const Icon(Icons.circle, size: 8, color: red) : null) : Text(trailing),
        onTap: onTap ?? (() => _go(v!)),
      );
    }

    Future<void> edit(int step) async {
      Navigator.of(context).pop();
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => OnboardingScreen(state: st, only: step)));
    }

    final savedCount = st.bookmarks.where((b) => b.lang == st.lang).length;
    return Drawer(
      child: Column(children: [
        Container(
          color: const Color(0xFF111111),
          padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 16, 8, 14),
          child: Row(children: [
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(s.t('menu'), style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
                if (feed?.generatedAt != null)
                  Text(s.updated(feed!.generatedAt!), style: const TextStyle(color: Colors.white60, fontSize: 12)),
              ]),
            ),
            IconButton(
              icon: const Icon(Icons.close, color: Colors.white),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ]),
        ),
        Expanded(
          child: ListView(padding: EdgeInsets.zero, children: [
            header(s.t('feeds')),
            item(s.t('myFeed'), 'myfeed'),
            item(s.t('allNews'), 'top'),
            if (st.province != null) item(s.provinceName(st.province!), 'province'),
            item(s.t('saved'), 'saved', trailing: savedCount > 0 ? '$savedCount' : null),
            header(s.t('cats')),
            for (final id in topicIds) item(s.topic(id), id),
            header(s.t('settings')),
            item(s.t('language'), null, trailing: st.lang == 'fr' ? 'Français' : 'English', onTap: () => edit(0)),
            item(s.t('province'), null,
                trailing: st.province == null ? s.t('none') : s.provinceName(st.province!), onTap: () => edit(1)),
            item(s.t('editTopics'), null, trailing: '${st.topics.length}', onTap: () => edit(2)),
            item(s.t('about'), null, onTap: () {
              Navigator.of(context).pop();
              Navigator.of(context).push(MaterialPageRoute(builder: (_) => SettingsScreen(state: st)));
            }),
            const SizedBox(height: 24),
          ]),
        ),
      ]),
    );
  }
}
