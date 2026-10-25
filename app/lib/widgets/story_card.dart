import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config.dart';
import '../models/story.dart';
import '../services/app_state.dart';
import 'bias_bar.dart';

/// One full-screen news card, Inshorts style: picture, source tab, bookmark /
/// share / report, headline, 60-word summary, coverage line, and a bottom strip
/// that opens the full article inside the app.
class StoryCard extends StatelessWidget {
  const StoryCard({super.key, required this.story, required this.state});
  final Story story;
  final AppState state;

  static const red = Color(0xFFE8412C);

  void _toast(BuildContext context, String msg) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(msg), duration: const Duration(milliseconds: 1400)));
  }

  Future<void> _openArticle() async {
    final uri = Uri.tryParse(story.readMoreUrl);
    if (uri == null || !(uri.scheme == 'https' || uri.scheme == 'http')) return;
    // Opens inside the app (Chrome Custom Tab), so readers don't leave.
    await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
  }

  Future<void> _report() async {
    final subject = Uri.encodeComponent('Report: story ${story.id} (${story.lang})');
    final body = Uri.encodeComponent('${story.headline}\n${story.readMoreUrl}\n\nWhat is wrong?\n');
    await launchUrl(Uri.parse('mailto:$contactEmail?subject=$subject&body=$body'));
  }

  @override
  Widget build(BuildContext context) {
    final s = state.s;
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final by = switch (story.summaryBy) {
      'editor' => s.t('editor'),
      'ai' => s.t('ai'),
      _ => s.t('excerpt'),
    };
    final saved = state.isSaved(story);
    final source = story.leadSource.isEmpty ? '?' : story.leadSource;

    return LayoutBuilder(
      builder: (context, box) => ColoredBox(
        color: cs.surface,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Picture with the source tab and the action tab sitting on its bottom edge.
            SizedBox(
              height: box.maxHeight * 0.33,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (story.imageUrl != null)
                    CachedNetworkImage(
                      imageUrl: story.imageUrl!,
                      fit: BoxFit.cover,
                      placeholder: (_, __) => Container(color: const Color(0xFF3A3A3C)),
                      errorWidget: (_, __, ___) => Container(color: const Color(0xFF3A3A3C)),
                    )
                  else
                    Container(
                      color: const Color(0xFF2C2C2E),
                      alignment: Alignment.center,
                      child: Text(source,
                          style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w700)),
                    ),
                  Positioned(
                    left: 16,
                    bottom: 0,
                    child: _Tab(
                      color: cs.surface,
                      child: Row(mainAxisSize: MainAxisSize.min, children: [
                        Container(
                          width: 18,
                          height: 18,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(color: red, borderRadius: BorderRadius.circular(4)),
                          child: Text(source.characters.first.toUpperCase(),
                              style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800)),
                        ),
                        const SizedBox(width: 8),
                        ConstrainedBox(
                          constraints: BoxConstraints(maxWidth: box.maxWidth * 0.45),
                          child: Text(source,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                        ),
                      ]),
                    ),
                  ),
                  Positioned(
                    right: 16,
                    bottom: 0,
                    child: _Tab(
                      color: cs.surface,
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Row(mainAxisSize: MainAxisSize.min, children: [
                        _IconBtn(
                          icon: saved ? Icons.bookmark : Icons.bookmark_border,
                          tip: s.t('saved'),
                          onTap: () async {
                            final now = await state.toggleBookmark(story);
                            if (context.mounted) _toast(context, s.t(now ? 'savedT' : 'unsavedT'));
                          },
                        ),
                        _IconBtn(
                          icon: Icons.share_outlined,
                          tip: 'Share',
                          onTap: () async {
                            await Clipboard.setData(
                                ClipboardData(text: '${story.headline}\n${story.readMoreUrl}\n— Canada Shorts'));
                            if (context.mounted) _toast(context, s.t('copied'));
                          },
                        ),
                        _IconBtn(icon: Icons.flag_outlined, tip: s.t('report'), onTap: _report),
                      ]),
                    ),
                  ),
                ],
              ),
            ),
            // Headline, summary, byline, coverage.
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 14, 22, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(story.headline,
                        style: TextStyle(fontSize: 20, height: 1.32, fontWeight: FontWeight.w600, color: cs.onSurface)),
                    const SizedBox(height: 10),
                    Text(story.summary,
                        style: TextStyle(
                            fontSize: 16, height: 1.6, fontWeight: FontWeight.w300, color: cs.onSurface.withValues(alpha: 0.82))),
                    const SizedBox(height: 10),
                    Text.rich(
                      TextSpan(children: [
                        TextSpan(text: s.t('shortBy'), style: TextStyle(fontWeight: FontWeight.w500, color: cs.onSurface)),
                        TextSpan(text: ' / ${s.ago(story.publishedAt)} · $by'),
                      ]),
                      style: TextStyle(fontSize: 12, color: cs.onSurfaceVariant),
                    ),
                    const SizedBox(height: 8),
                    CoverageLine(bias: story.bias, s: s),
                  ],
                ),
              ),
            ),
            // "Read the full story" strip.
            Material(
              color: const Color(0xFF2A2A2A),
              child: InkWell(
                onTap: _openArticle,
                child: SizedBox(
                  height: 64,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 22),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(s.readAt(source),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: Colors.white, fontSize: 15)),
                        Text(s.t('tapHere'), style: const TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  const _Tab({required this.child, required this.color, this.padding = const EdgeInsets.symmetric(horizontal: 14)});
  final Widget child;
  final Color color;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) => Container(
        height: 36,
        padding: padding,
        decoration: BoxDecoration(color: color, borderRadius: const BorderRadius.vertical(top: Radius.circular(14))),
        child: Center(child: child),
      );
}

class _IconBtn extends StatelessWidget {
  const _IconBtn({required this.icon, required this.tip, required this.onTap});
  final IconData icon;
  final String tip;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => IconButton(
        icon: Icon(icon, size: 21),
        tooltip: tip,
        visualDensity: VisualDensity.compact,
        onPressed: onTap,
      );
}
