"""
Unified multi-tier data loader.
Handles LiDAR zip/folder captures, Monocular Video MP4s, and Sparse Photo Folders.
"""

import os
import io
import csv
import zipfile
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional, Tuple
from scipy.spatial.transform import Rotation as R


class CaptureDataLoader:
    """Loads raw sensor data, poses, images, and intrinsics across input tiers."""

    def __init__(self, capture_path: str):
        self.capture_path = capture_path
        self.is_zip = zipfile.is_zipfile(capture_path) if os.path.exists(capture_path) else False
        self.zip_ref = zipfile.ZipFile(capture_path, 'r') if self.is_zip else None
        
        # Determine scan prefix if in zip or directory
        self.prefix = self._determine_prefix()
        self.camera_matrix: Optional[np.ndarray] = None
        self.poses: Dict[str, Tuple[np.ndarray, np.ndarray, float]] = {} # frame -> (pos, rot_matrix, timestamp)
        self.imu_data: List[Dict[str, float]] = []
        
        self._load_metadata()

    def _determine_prefix(self) -> str:
        if self.is_zip and self.zip_ref:
            nl = self.zip_ref.namelist()
            return nl[0].split('/')[0] if nl else ""
        elif os.path.isdir(self.capture_path):
            subdirs = [d for d in os.listdir(self.capture_path) if os.path.isdir(os.path.join(self.capture_path, d))]
            return subdirs[0] if subdirs else ""
        return ""

    def _read_text_file(self, rel_path: str) -> Optional[List[str]]:
        candidates = [
            f"{self.prefix}/{rel_path}" if self.prefix else rel_path,
            rel_path,
            os.path.basename(rel_path)
        ]
        
        if self.is_zip and self.zip_ref:
            for c in candidates:
                if c in self.zip_ref.namelist():
                    data = self.zip_ref.read(c).decode('utf-8', errors='ignore')
                    return [line.strip() for line in data.strip().split('\n') if line.strip()]
        else:
            base_dir = self.capture_path
            for c in candidates:
                p = os.path.join(base_dir, c)
                if os.path.isfile(p):
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        return [line.strip() for line in f.readlines() if line.strip()]
        return None

    def _load_metadata(self):
        # 1. Camera Matrix
        cam_lines = self._read_text_file("camera_matrix.csv")
        if cam_lines:
            rows = []
            for line in cam_lines:
                vals = [float(v.strip()) for v in line.split(',') if v.strip()]
                if vals:
                    rows.append(vals)
            if len(rows) >= 3:
                self.camera_matrix = np.array(rows[:3])

        # 2. Odometry
        odo_lines = self._read_text_file("odometry.csv")
        if odo_lines and len(odo_lines) > 1:
            header = [c.strip() for c in odo_lines[0].split(',')]
            frame_idx = header.index('frame') if 'frame' in header else 1
            t_idx = header.index('timestamp') if 'timestamp' in header else 0
            x_idx = header.index('x') if 'x' in header else 2
            y_idx = header.index('y') if 'y' in header else 3
            z_idx = header.index('z') if 'z' in header else 4
            qx_idx = header.index('qx') if 'qx' in header else 5
            qy_idx = header.index('qy') if 'qy' in header else 6
            qz_idx = header.index('qz') if 'qz' in header else 7
            qw_idx = header.index('qw') if 'qw' in header else 8

            for line in odo_lines[1:]:
                row = [c.strip() for c in line.split(',')]
                if len(row) <= qw_idx:
                    continue
                try:
                    fnum = f"{int(row[frame_idx]):06d}"
                    ts = float(row[t_idx])
                    pos = np.array([float(row[x_idx]), float(row[y_idx]), float(row[z_idx])])
                    quat = [float(row[qx_idx]), float(row[qy_idx]), float(row[qz_idx]), float(row[qw_idx])]
                    rot = R.from_quat(quat).as_matrix()
                    self.poses[fnum] = (pos, rot, ts)
                except ValueError:
                    continue

        # 3. IMU
        imu_lines = self._read_text_file("imu.csv")
        if imu_lines and len(imu_lines) > 1:
            header = [c.strip() for c in imu_lines[0].split(',')]
            for line in imu_lines[1:]:
                row = [c.strip() for c in line.split(',')]
                if len(row) == len(header):
                    try:
                        self.imu_data.append({header[i]: float(row[i]) for i in range(len(header))})
                    except ValueError:
                        continue

    def get_frame_ids(self) -> List[str]:
        """Returns sorted list of available depth or pose frame IDs."""
        if self.poses:
            return sorted(list(self.poses.keys()))
        elif self.is_zip and self.zip_ref:
            depth_files = [f for f in self.zip_ref.namelist() if '/depth/' in f and f.endswith('.png')]
            return sorted([os.path.basename(f).replace('.png', '') for f in depth_files])
        return []

    def get_depth_and_confidence(self, frame_id: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Loads depth map (in meters) and confidence map for given frame."""
        depth_name = f"{self.prefix}/depth/{frame_id}.png" if self.prefix else f"depth/{frame_id}.png"
        conf_name = f"{self.prefix}/confidence/{frame_id}.png" if self.prefix else f"confidence/{frame_id}.png"

        depth_arr = None
        conf_arr = None

        if self.is_zip and self.zip_ref:
            if depth_name in self.zip_ref.namelist():
                img_d = Image.open(io.BytesIO(self.zip_ref.read(depth_name)))
                depth_arr = np.array(img_d, dtype=np.float32) / 1000.0 # mm to meters
            if conf_name in self.zip_ref.namelist():
                img_c = Image.open(io.BytesIO(self.zip_ref.read(conf_name)))
                conf_arr = np.array(img_c)
        else:
            p_depth = os.path.join(self.capture_path, depth_name)
            p_conf = os.path.join(self.capture_path, conf_name)
            if os.path.exists(p_depth):
                img_d = Image.open(p_depth)
                depth_arr = np.array(img_d, dtype=np.float32) / 1000.0
            if os.path.exists(p_conf):
                img_c = Image.open(p_conf)
                conf_arr = np.array(img_c)

        return depth_arr, conf_arr

    def close(self):
        if self.zip_ref:
            self.zip_ref.close()
