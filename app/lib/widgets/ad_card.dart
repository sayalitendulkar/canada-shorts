import 'package:flutter/material.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import '../config.dart';
import '../l10n.dart';

/// A full card with one clearly labelled ad (300x250), shown every [adEvery]
/// stories. Uses Google's test ad unit until real AdMob IDs are set.
class AdCard extends StatefulWidget {
  const AdCard({super.key, required this.s});
  final S s;

  @override
  State<AdCard> createState() => _AdCardState();
}

class _AdCardState extends State<AdCard> {
  BannerAd? _ad;
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    _ad = BannerAd(
      adUnitId: bannerAdUnitId,
      size: AdSize.mediumRectangle,
      request: const AdRequest(keywords: ['news', 'canada']),
      listener: BannerAdListener(
        onAdLoaded: (_) {
          if (mounted) setState(() => _loaded = true);
        },
        onAdFailedToLoad: (ad, error) {
          ad.dispose();
          _ad = null;
        },
      ),
    )..load();
  }

  @override
  void dispose() {
    _ad?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return ColoredBox(
      color: cs.surfaceContainerLow,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(color: const Color(0xFFFFD54F), borderRadius: BorderRadius.circular(4)),
              child: Text(widget.s.t('ad'), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.black)),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: AdSize.mediumRectangle.width.toDouble(),
              height: AdSize.mediumRectangle.height.toDouble(),
              child: _loaded && _ad != null
                  ? AdWidget(ad: _ad!)
                  : Center(child: CircularProgressIndicator(strokeWidth: 2, color: cs.outline)),
            ),
            const SizedBox(height: 20),
            Text(widget.s.t('adNext'), style: TextStyle(fontSize: 13, color: cs.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}
