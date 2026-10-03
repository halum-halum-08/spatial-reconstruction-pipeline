#!/usr/bin/env python3
"""
Single-Command CLI Entrypoint for Cold Capture Processing.
Usage:
    python scripts/run_capture.py --input <path> [--tier lidar|video|photo] [--output <dir>]
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tiers.lidar_pipeline import LidarPipeline
from tiers.video_pipeline import VideoPipeline
from tiers.photo_pipeline import PhotoPipeline


def auto_detect_tier(input_path: str) -> str:
    """Infers input tier from path and contents."""
    if os.path.isfile(input_path):
        if input_path.lower().endswith('.mp4'):
            return "video"
        elif input_path.lower().endswith('.zip'):
            return "lidar"
    elif os.path.isdir(input_path):
        subdirs = [os.path.join(input_path, d) for d in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, d))]
        # Check if subdirs contain image stills
        has_sub_photos = any(
            any(f.lower().endswith(('.jpg', '.jpeg', '.png')) for f in os.listdir(sd))
            for sd in subdirs if os.path.isdir(sd)
        )
        if has_sub_photos:
            return "photo"
        if os.path.exists(os.path.join(input_path, "odometry.csv")):
            return "lidar"
        if os.path.exists(os.path.join(input_path, "rgb.mp4")):
            return "lidar"
    return "lidar" # Default fallback


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Multi-Tier 3D Reconstruction and Inspection Engine"
    )
    parser.add_argument("--input", "-i", required=True, help="Path to capture file (.zip, .mp4, or photo folder)")
    parser.add_argument("--tier", "-t", choices=["lidar", "video", "photo", "auto"], default="auto", help="Input sensor tier")
    parser.add_argument("--output", "-o", default=None, help="Directory to save generated outputs")
    parser.add_argument("--disable-drift-correction", action="store_true", help="Ablation: Disable drift correction")
    parser.add_argument("--ground-truth", default="benchmark_data/ground_truth.json", help="Path to ground truth JSON")

    args = parser.parse_args()

    tier = args.tier
    if tier == "auto":
        tier = auto_detect_tier(args.input)
        print(f"[*] Auto-detected input sensor tier: {tier.upper()}")

    out_dir = args.output or f"outputs/{tier}"
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n========================================================")
    print(f"  RUNNING CAPTURE PIPELINE")
    print(f"  Input:  {args.input}")
    print(f"  Tier:   {tier.upper()}")
    print(f"  Output: {out_dir}")
    print(f"========================================================\n")

    if tier == "lidar":
        pipeline = LidarPipeline(enable_drift_correction=not args.disable_drift_correction)
        plan = pipeline.run(args.input, ground_truth_path=args.ground_truth, output_dir=out_dir)
    elif tier == "video":
        pipeline = VideoPipeline()
        plan = pipeline.run(args.input, ground_truth_path=args.ground_truth, output_dir=out_dir)
    elif tier == "photo":
        pipeline = PhotoPipeline()
        plan = pipeline.run(args.input, ground_truth_path=args.ground_truth, output_dir=out_dir)
    else:
        raise ValueError(f"Unsupported tier: {tier}")

    print("\n[✓] Capture processing successful!")
    print(f"    - Rooms Mapped: {len(plan.rooms)}")
    print(f"    - Total Floor Area: {plan.total_floor_area.value:.2f} m² (CI: [{plan.total_floor_area.ci_lower:.2f}, {plan.total_floor_area.ci_upper:.2f}] {plan.total_floor_area.unit})")
    print(f"    - Walls Bounded: {plan.total_walls_count}")
    print(f"    - Openings Detected: {plan.total_openings_count}")
    print(f"    - Remediation Scope Total: ${plan.remediation_total_usd:,.2f}")
    print(f"    - Plan JSON:   {os.path.join(out_dir, 'property_plan.json')}")
    print(f"    - Plan SVG:    {os.path.join(out_dir, 'floorplan.svg')}")
    print(f"    - Viewer HTML: {os.path.join(out_dir, 'index.html')}")


if __name__ == "__main__":
    main()
