import zipfile
import csv
import io
import numpy as np

zips = {
    'c00a170fe1 (single_room)': 'single_room.zip',
    '1a8384c3f6 (floor_only)': 'single_scan_floor_only.zip',
    'c7d28f72c6 (with_ceiling)': 'single_scan_with_ceiling.zip'
}

for name, zpath in zips.items():
    with zipfile.ZipFile(zpath, 'r') as z:
        prefix = name.split()[0]
        odo_text = z.read(f"{prefix}/odometry.csv").decode('utf-8').strip().split('\n')
        reader = csv.reader(odo_text)
        header = [h.strip() for h in next(reader)]
        
        # columns: timestamp, frame, x, y, z, qx, qy, qz, qw ...
        x_idx = header.index('x')
        y_idx = header.index('y')
        z_idx = header.index('z')
        
        pts = []
        for row in reader:
            if row and len(row) > z_idx:
                pts.append([float(row[x_idx]), float(row[y_idx]), float(row[z_idx])])
        pts = np.array(pts)
        
        print(f"\n=== {name} ===")
        print(f"Points count: {len(pts)}")
        print(f"Start pos: {pts[0]}")
        print(f"End pos:   {pts[-1]}")
        dist_start_end = np.linalg.norm(pts[0] - pts[-1])
        print(f"Loop closure distance (start to end): {dist_start_end:.3f} m")
        min_bound = np.min(pts, axis=0)
        max_bound = np.max(pts, axis=0)
        span = max_bound - min_bound
        print(f"Min (x,y,z): {min_bound}")
        print(f"Max (x,y,z): {max_bound}")
        print(f"Bounding span: dx={span[0]:.2f}m, dy={span[1]:.2f}m, dz={span[2]:.2f}m")
        # Trajectory path length
        diffs = np.diff(pts, axis=0)
        path_len = np.sum(np.linalg.norm(diffs, axis=1))
        print(f"Total trajectory path length: {path_len:.2f} m")
