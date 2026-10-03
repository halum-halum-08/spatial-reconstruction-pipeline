"""
Calibration and Uncertainty Propagation Engine.
Ensures honest confidence intervals across input tiers:
- LiDAR Tier: High precision, tight CIs (~±1 cm)
- Video Tier: Medium precision, widened CIs (~±3%)
- Photo Tier: Thin sparse input, honestly widened CIs (~±8%)
"""

import numpy as np
from pipeline.schema import MeasurementWithCI


class CalibrationEngine:
    """Computes measurement estimates and honest confidence intervals."""

    def __init__(self, tier: str = "lidar"):
        self.tier = tier.lower()
        
        # Base standard error multipliers per tier
        if self.tier == "lidar":
            self.linear_rel_std = 0.0035  # ~0.35% relative error
            self.linear_abs_std = 0.0070  # ~7 mm base absolute noise
            self.height_abs_std = 0.0055  # ~5.5 mm ceiling height noise
            self.opening_abs_std = 0.0085 # ~8.5 mm opening width noise
            self.area_rel_std = 0.0080    # ~0.8% area uncertainty
        elif self.tier == "video":
            self.linear_rel_std = 0.0180  # ~1.8% relative error
            self.linear_abs_std = 0.0250  # ~2.5 cm base absolute noise
            self.height_abs_std = 0.0220  # ~2.2 cm ceiling height noise
            self.opening_abs_std = 0.0280 # ~2.8 cm opening width noise
            self.area_rel_std = 0.0350    # ~3.5% area uncertainty
        elif self.tier == "photo":
            self.linear_rel_std = 0.0420  # ~4.2% relative error
            self.linear_abs_std = 0.0550  # ~5.5 cm base absolute noise
            self.height_abs_std = 0.0480  # ~4.8 cm ceiling height noise
            self.opening_abs_std = 0.0620 # ~6.2 cm opening width noise
            self.area_rel_std = 0.0750    # ~7.5% area uncertainty
        else:
            raise ValueError(f"Unknown input tier: {tier}")

    def measure_length(self, value: float) -> MeasurementWithCI:
        """Wall length measurement with calibrated CI."""
        std_err = np.sqrt(self.linear_abs_std**2 + (self.linear_rel_std * value)**2)
        return MeasurementWithCI.create(value, std_err, unit="m")

    def measure_height(self, value: float) -> MeasurementWithCI:
        """Ceiling height measurement with calibrated CI."""
        std_err = np.sqrt(self.height_abs_std**2 + (0.002 * value)**2)
        return MeasurementWithCI.create(value, std_err, unit="m")

    def measure_opening(self, value: float) -> MeasurementWithCI:
        """Opening (door/window) width measurement with calibrated CI."""
        std_err = np.sqrt(self.opening_abs_std**2 + (self.linear_rel_std * value)**2)
        return MeasurementWithCI.create(value, std_err, unit="m")

    def measure_area(self, value: float) -> MeasurementWithCI:
        """Floor surface area measurement with propagated CI."""
        std_err = value * self.area_rel_std
        return MeasurementWithCI.create(value, std_err, unit="m2")
