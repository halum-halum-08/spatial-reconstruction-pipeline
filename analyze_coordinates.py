import csv
import numpy as np
from scipy.spatial.transform import Rotation as R

def analyze_scan(scan_dir):
    odo_path = f"{scan_dir}/odometry.csv"
    with open(odo_path, 'r') as f:
        reader = csv.reader(f)
        header = [h.strip() for h in next(reader)]
        
        t_idx = header.index('timestamp')
        x_idx = header.index('x')
        y_idx = header.index('y')
        z_idx = header.index('z')
        qx_idx = header.index('qx')
        qy_idx = header.index('qy')
        qz_idx = header.index('qz')
        qw_idx = header.index('qw')
        
        positions = []
        forward_vecs = []
        up_vecs = []
        
        for row in reader:
            if not row or len(row) <= qw_idx:
                continue
            pos = [float(row[x_idx]), float(row[y_idx]), float(row[z_idx])]
            quat = [float(row[qx_idx]), float(row[qy_idx]), float(row[qz_idx]), float(row[qw_idx])]
            rot = R.from_quat(quat)
            # In camera frame, camera looks along -Z (or +Z), camera up is +Y
            # Let's check rotation matrix:
            # rot.apply([0, 0, -1]) is camera forward in world coordinates
            # rot.apply([0, 1, 0]) is camera up in world coordinates
            fwd = rot.apply([0, 0, -1])
            up = rot.apply([0, 1, 0])
            
            positions.append(pos)
            forward_vecs.append(fwd)
            up_vecs.append(up)
            
    positions = np.array(positions)
    forward_vecs = np.array(forward_vecs)
    up_vecs = np.array(up_vecs)
    
    print(f"\n--- Analysis for {scan_dir} ---")
    print(f"Num poses: {len(positions)}")
    print(f"Position ranges:")
    print(f"  X: min={positions[:,0].min():.3f}, max={positions[:,0].max():.3f}, span={positions[:,0].max()-positions[:,0].min():.3f}")
    print(f"  Y: min={positions[:,1].min():.3f}, max={positions[:,1].max():.3f}, span={positions[:,1].max()-positions[:,1].min():.3f}")
    print(f"  Z: min={positions[:,2].min():.3f}, max={positions[:,2].max():.3f}, span={positions[:,2].max()-positions[:,2].min():.3f}")
    print(f"Mean Up vector in world frame: {np.mean(up_vecs, axis=0)}")
    print(f"Mean Forward vector in world frame: {np.mean(forward_vecs, axis=0)}")
    
for s in ['data/c00a170fe1', 'data/1a8384c3f6', 'data/c7d28f72c6']:
    analyze_scan(s)
