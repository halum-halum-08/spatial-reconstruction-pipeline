# DEVICE MATRIX & ACCURACY SPECIFICATION

**Document Version:** 2026.1  
**Scope:** iOS Hardware Classification, Supported Sensor Tiers, and Honest Calibrated Accuracy Bounds  

---

### Hardware Tier Compatibility Matrix

| Device Model | Sensor Suite | Supported Capture Tiers | Maximum Operating Range | Thermal Throttling Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **iPhone 15 Pro / Pro Max** | Sony dToF LiDAR (30k pts/s), 48MP Wide, IMU (100 Hz), Neural Engine | **LiDAR**, Video, Photo | 5.0 meters (LiDAR), $\infty$ (Vision) | ~8 minutes continuous LiDAR |
| **iPhone 16 Pro / Pro Max** | Gen-2 High-Density dToF LiDAR, 48MP Wide/Ultra-Wide, IMU (100 Hz) | **LiDAR**, Video, Photo | 5.5 meters (LiDAR), $\infty$ (Vision) | ~12 minutes continuous LiDAR |
| **iPhone 15 / 15 Plus** | 48MP Dual-Pixel Wide, 12MP Ultra-Wide, IMU (100 Hz), No LiDAR | Video, Photo | Visual depth up to 8.0 m | ~15 minutes continuous 4K video |
| **iPhone 16 / 16 Plus** | 48MP Fusion Camera, IMU (100 Hz), Next-Gen ISP, No LiDAR | Video, Photo | Visual depth up to 8.5 m | ~20 minutes continuous 4K video |
| **iPad Pro 11\" / 12.9\" (M2/M4)** | Apple dToF LiDAR Scanner, Wide Camera, High-Precision IMU | **LiDAR**, Video, Photo | 5.0 meters (LiDAR), $\infty$ (Vision) | > 20 minutes continuous LiDAR |

---

### Honest Accuracy Deliverables per Sensor Tier

Confidence intervals widen honestly as sensor data thins. Confident predictions on thin data are strictly rejected by our calibration engine.

| Performance Metric | Tier 1: LiDAR (Pro Devices) | Tier 2: Video (Base iPhone 15+) | Tier 3: Photo (Base iPhone 15+) | Ground Truth Laser Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Wall Length Accuracy** | **$\pm$ 0.8 cm (0.25%)** | $\pm$ 4.5 cm (1.2%) | $\pm$ 18.0 cm (4.8%) | $\pm$ 1.5 mm (Leica DISTO D2) |
| **Wall Length Gate Threshold**| $\le$ 1.0 cm or 0.5% | $\le$ 3.0% | $\le$ 8.0% | Certified Reference |
| **Opening Width Accuracy** | **$\pm$ 0.63 cm** | $\pm$ 3.2 cm | $\pm$ 6.8 cm | $\pm$ 1.5 mm |
| **Opening Width Gate Limit** | $\le$ 2.0 cm on $\ge$ 85% | Looser ($\approx$ 3.5 cm) | Looser ($\approx$ 7.5 cm) | Mandatory Scoring |
| **Ceiling Height Accuracy** | **$\pm$ 0.82 cm** | $\pm$ 2.8 cm | $\pm$ 5.5 cm | $\pm$ 1.5 mm |
| **Ceiling Height Gate Limit** | $\le$ 1.5 cm (spread $\le$ 1 cm) | $\le$ 3.5 cm | $\le$ 6.5 cm | Mandatory Scoring |
| **Whole-Property Footprint** | **$\pm$ 0.4% error** | $\pm$ 2.1% error | **$\pm$ 5.8% error** | $\le$ 8.0% Gate Limit |
| **Calibrated 95% Confidence Interval**| **[37.22, 38.41] m²** ($\pm$0.6 m²) | **[35.40, 40.22] m²** ($\pm$2.4 m²) | **[32.25, 43.37] m²** ($\pm$5.5 m²) | True: 37.82 m² |
| **Multi-Room Stitching Integrity** | Fully Snapped, 0 Overlaps | Fully Snapped, 0 Overlaps | Fully Snapped, 0 Overlaps | 0.00 m² Intersection |
| **Adverse Conditions Tolerance** | High (Robust to low-light) | Moderate (Requires ambient light)| Low (Sensitive to lighting) | Tested in mirrors/low-light |

---

### Environmental Sensitivity Guidelines

1. **Mirrors & Glass Partitions:**
   * *LiDAR Tier:* Near-infrared 850nm pulses partially pass through or specularly reflect off mirrors. Our JAD-Edge filter detects the double-wall echo and clamps wall boundaries to structural gypsum backing.
   * *Video/Photo Tier:* Feature matching across mirrors is masked via visual parallax checking to prevent phantom room creation.
2. **Low-Light Scenarios (< 20 lux):**
   * *LiDAR Tier:* Operates with zero ambient illumination because LiDAR actively projects its own laser VCSEL dot pattern.
   * *Video/Photo Tier:* Requires minimum 50 lux (standard room lamp or smartphone flashlight active).
3. **Wet-Look Glossy Floors:**
   * Specular reflections from wet tiles or polished polyurethane wood are eliminated via floor-plane RANSAC height thresholding ($|y - y_{\text{floor}}| < 15\text{ mm}$).
