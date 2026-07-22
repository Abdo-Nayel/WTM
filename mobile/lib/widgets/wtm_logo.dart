import 'package:flutter/material.dart';

import '../core/branding/brand.dart';

/// WorkTaskMe mark: geometric W merging into an upward arrow + check.
///
/// Prefer SVG/PNG assets when available; this painter keeps UI working offline.
class WtmLogo extends StatelessWidget {
  const WtmLogo({
    super.key,
    this.size = 72,
    this.showWordmark = false,
    this.wordmarkColor,
    this.compact = false,
    this.useAsset = true,
  });

  final double size;
  final bool showWordmark;
  final Color? wordmarkColor;

  /// When true, shows short name "WTM" instead of "WorkTaskMe".
  final bool compact;

  /// Prefer raster/SVG asset from `assets/images/` when present.
  final bool useAsset;

  @override
  Widget build(BuildContext context) {
    final mark = SizedBox(
      width: size,
      height: size,
      child: useAsset
          ? Image.asset(
              'assets/images/worktaskme-icon.png',
              width: size,
              height: size,
              fit: BoxFit.contain,
              errorBuilder: (_, __, ___) => CustomPaint(painter: _WtmMarkPainter()),
            )
          : CustomPaint(painter: _WtmMarkPainter()),
    );

    if (!showWordmark) return mark;

    final name = compact ? Brand.shortName : Brand.productName;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        mark,
        SizedBox(height: size * 0.18),
        Text(
          name,
          style: TextStyle(
            fontSize: compact ? size * 0.38 : size * 0.32,
            fontWeight: FontWeight.w800,
            letterSpacing: compact ? 1.2 : -0.8,
            color: wordmarkColor ?? BrandColors.primary,
          ),
        ),
      ],
    );
  }
}

class _WtmMarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final s = size.shortestSide;
    final r = Radius.circular(s * 0.22);

    final bg = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFF4338CA), BrandColors.primary, Color(0xFF3730A3)],
      ).createShader(Offset.zero & size);

    canvas.drawRRect(RRect.fromRectAndRadius(Offset.zero & size, r), bg);

    // Soft constellation dots
    final dot = Paint()..color = const Color(0xFFA5B4FC).withOpacity(0.45);
    canvas.drawCircle(Offset(s * 0.18, s * 0.2), s * 0.012, dot);
    canvas.drawCircle(Offset(s * 0.32, s * 0.14), s * 0.01, dot);
    canvas.drawCircle(Offset(s * 0.82, s * 0.18), s * 0.012, dot);

    final markPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: const [
          Color(0xFFEEF2FF),
          Color(0xFFC7D2FE),
          Color(0xFF34D399),
          BrandColors.accent,
        ],
        stops: const [0, 0.45, 0.72, 1],
      ).createShader(Offset.zero & size);

    // Simplified W → arrow silhouette
    final w = Path()
      ..moveTo(s * 0.22, s * 0.74)
      ..lineTo(s * 0.30, s * 0.30)
      ..lineTo(s * 0.40, s * 0.30)
      ..lineTo(s * 0.50, s * 0.58)
      ..lineTo(s * 0.60, s * 0.30)
      ..lineTo(s * 0.70, s * 0.30)
      ..lineTo(s * 0.78, s * 0.48)
      ..lineTo(s * 0.86, s * 0.34)
      ..lineTo(s * 0.94, s * 0.42)
      ..lineTo(s * 0.78, s * 0.60)
      ..lineTo(s * 0.68, s * 0.54)
      ..lineTo(s * 0.62, s * 0.70)
      ..lineTo(s * 0.48, s * 0.78)
      ..lineTo(s * 0.38, s * 0.70)
      ..lineTo(s * 0.30, s * 0.48)
      ..lineTo(s * 0.26, s * 0.74)
      ..close();
    canvas.drawPath(w, markPaint);

    // Person cue cutout on left stem
    canvas.drawCircle(
      Offset(s * 0.27, s * 0.62),
      s * 0.035,
      Paint()..color = BrandColors.primary,
    );

    // Emerald check
    final check = Paint()
      ..color = BrandColors.accent
      ..style = PaintingStyle.stroke
      ..strokeWidth = s * 0.07
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final checkPath = Path()
      ..moveTo(s * 0.48, s * 0.56)
      ..lineTo(s * 0.58, s * 0.66)
      ..lineTo(s * 0.78, s * 0.42);
    canvas.drawPath(checkPath, check);

    final checkHi = Paint()
      ..color = const Color(0xFFECFDF5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = s * 0.03
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(checkPath, checkHi);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
