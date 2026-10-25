import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/story.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';
import 'bias_bar.dart';

/// One full-screen card: image, headline, <=60-word summary, source + time,
/// bias bar, and actions. Source name and date on every card are required by
/// Google Play's news policy.
class StoryCard extends StatelessWidget {
  const StoryCard({super.key, required this.story, required this.state, required this.api});
  final Story story;
  final AppState state;
  final ApiClient api;

  Future<void> _open(BuildContext context, String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null || !(uri.scheme == 'https' || uri.scheme == 'http')) return;
    await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
  }

  Future<void> _report(BuildContext context) async {
    final s = state.s;
    final controller = TextEditingController();
    final reason = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.t('report')),
        content: TextField(
          controller: controller,
          maxLines: 3,
          maxLength: 500,
          decoration: InputDecoration(hintText: s.t('reportHint')),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(s.t('cancel'))),
          FilledButton(onPressed: () => Navigator.pop(ctx, controller.text.trim()), child: Text(s.t('send'))),
        ],
      ),
    );
    controller.dispose();
    if (reason == null || reason.length < 3) return;
    try {
      await api.report(story.id, reason);
    } catch (_) {
      // Fail quietly; a production build would queue and retry.
    }
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(s.t('thanks'))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = state.s;
    final theme = Theme.of(context);
    final label = switch (story.summaryBy) {
      'editor' => s.t('editorLabel'),
      'ai' => s.t('aiLabel'),
      _ => s.t('excerptLabel'),
    };
    return LayoutBuilder(
      builder: (context, box) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            height: box.maxHeight * 0.36,
            child: story.imageUrl == null
                ? Container(
                    color: theme.colorScheme.primaryContainer,
                    alignment: Alignment.center,
                    child: Text(story.leadSource, style: theme.textTheme.titleLarge),
                  )
                : CachedNetworkImage(
                    imageUrl: story.imageUrl!,
                    fit: BoxFit.cover,
                    errorWidget: (_, __, ___) => Container(color: theme.colorScheme.primaryContainer),
                  ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(story.headline,
                      style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700, height: 1.25)),
                  const SizedBox(height: 12),
                  Expanded(
                    child: SingleChildScrollView(
                      physics: const NeverScrollableScrollPhysics(),
                      child: Text(story.summary, style: theme.textTheme.bodyLarge?.copyWith(height: 1.5)),
                    ),
                  ),
                  Text(
                    '${story.leadSource} · ${s.ago(story.publishedAt)} · $label',
                    style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  ),
                  const SizedBox(height: 8),
                  BiasBar(bias: story.bias, s: s),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            child: Row(
              children: [
                IconButton(
                  tooltip: s.t('saved'),
                  icon: Icon(state.isSaved(story) ? Icons.bookmark : Icons.bookmark_border),
                  onPressed: () => state.toggleBookmark(story),
                ),
                Builder(
                  builder: (bctx) => IconButton(
                    tooltip: 'Share',
                    icon: const Icon(Icons.share_outlined),
                    onPressed: () {
                      final b = bctx.findRenderObject() as RenderBox?;
                      Share.share(
                        '${story.headline}\n${story.readMoreUrl}\n— Canada Shorts',
                        sharePositionOrigin: b == null ? null : b.localToGlobal(Offset.zero) & b.size,
                      );
                    },
                  ),
                ),
                IconButton(
                  tooltip: s.t('report'),
                  icon: const Icon(Icons.flag_outlined),
                  onPressed: () => _report(context),
                ),
                const Spacer(),
                Flexible(
                  child: FilledButton.tonal(
                    onPressed: () => _open(context, story.readMoreUrl),
                    child: Text(s.t('readMore'), overflow: TextOverflow.ellipsis),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
