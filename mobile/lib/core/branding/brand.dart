import 'package:flutter/material.dart';

/// Product naming + brand colors for WorkTaskMe / WTM.
class Brand {
  Brand._();

  static const String productName = 'WorkTaskMe';
  static const String shortName = 'WTM';
  static const String tagline = 'Agile boards + team calendar';
}

class BrandColors {
  BrandColors._();

  /// Primary indigo
  static const Color primary = Color(0xFF4F46E5);

  /// Emerald accent
  static const Color accent = Color(0xFF10B981);

  /// Light scaffold
  static const Color backgroundLight = Color(0xFFF8FAFC);

  /// Dark scaffold (slate)
  static const Color backgroundDark = Color(0xFF0F172A);
}
