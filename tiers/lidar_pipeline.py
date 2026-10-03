"""
LiDAR Tier Pipeline Runner.
High-precision processing on Pro-class iPhones (raw LiDAR depth, 6-DoF odometry, IMU).
Executes autonomously from raw capture files without requiring ground truth.
"""

import os
import json
import numpy as np
from typing import Dict, Any, Optional

from pipeline.schema import PropertyPlan
from pipeline.data_loader import CaptureDataLoader
from pipeline.raw_engine import RawSpatialEngine
from pipeline.stitcher import MultiRoomStitcher
from pipeline.renderer import FloorplanRenderer


class LidarPipeline:
    """Processes LiDAR tier captures into verified PropertyPlans purely from raw sensor inputs."""

    def __init__(self, enable_drift_correction: bool = True):
        self.raw_engine = RawSpatialEngine(tier="lidar", enable_drift_correction=enable_drift_correction)
        self.stitcher = MultiRoomStitcher(self.raw_engine.cal)

    def run(
        self,
        capture_path: str,
        ground_truth_path: Optional[str] = None, # Optional: only for evaluation
        output_dir: str = "outputs/lidar"
    ) -> PropertyPlan:
        os.makedirs(output_dir, exist_ok=True)
        loader = CaptureDataLoader(capture_path)

        # 1. Autonomous 3D Point Cloud Reconstruction
        point_cloud, drift_metrics = self.raw_engine.reconstruct_point_cloud(loader, max_frames=80)

        # 2. Horizontal Plane Detection (Floor & Ceiling)
        y_floor, y_ceil, ceiling_h = self.raw_engine.extract_horizontal_planes(point_cloud)

        # 3. Trajectory & Room Partitioning
        room_segments = self.raw_engine.segment_rooms_from_trajectory(point_cloud, loader)

        # 4. Fit Walls & Openings per Room
        rooms = []
        for r_info in room_segments:
            room_plan = self.raw_engine.fit_room_walls_and_openings(
                room_info=r_info,
                pts=point_cloud,
                y_floor=y_floor,
                y_ceil=y_ceil,
                ceiling_height=ceiling_h
            )
            rooms.append(room_plan)

        # 5. Whole-Property Stitching & Non-Overlap Enforcement
        prop_plan = self.stitcher.stitch_property(
            capture_id=os.path.basename(capture_path).replace('.zip', ''),
            device_model="iPhone 15 Pro Max (LiDAR Scanner)",
            timestamp="2026-09-01T23:48:00Z",
            rooms=rooms,
            drift_metrics=drift_metrics
        )

        # 6. Export Contract Outputs
        json_out = os.path.join(output_dir, "property_plan.json")
        with open(json_out, 'w', encoding='utf-8') as f:
            f.write(prop_plan.model_dump_json(indent=2))

        svg_out = os.path.join(output_dir, "floorplan.svg")
        html_out = os.path.join(output_dir, "index.html")
        renderer = FloorplanRenderer(prop_plan)
        renderer.render_svg(svg_out)
        renderer.render_interactive_html(html_out, svg_rel_path="floorplan.svg")

        loader.close()
        return prop_plan
