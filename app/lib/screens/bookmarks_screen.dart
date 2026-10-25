import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/app_state.dart';
import '../widgets/story_card.dart';

class BookmarksScreen extends StatelessWidget {
  const BookmarksScreen({super.key, required this.state, required this.api});
  final AppState state;
  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final s = state.s;
        return Scaffold(
          appBar: AppBar(title: Text(s.t('bookmarks'))),
          body: state.bookmarks.isEmpty
              ? Center(child: Padding(padding: const EdgeInsets.all(32), child: Text(s.t('noBookmarks'))))
              : PageView.builder(
                  scrollDirection: Axis.vertical,
                  itemCount: state.bookmarks.length,
                  itemBuilder: (_, i) => StoryCard(story: state.bookmarks[i], state: state, api: api),
                ),
        );
      },
    );
  }
}
