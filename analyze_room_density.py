import csv
import numpy as np

def analyze_rooms_in_scan(csv_path):
    with open(csv_path) as f:
        r = csv.reader(f)
        h = [c.strip() for c in next(r)]
        t_idx = h.index('timestamp')
        x_idx = h.index('x')
        y_idx = h.index('y')
        z_idx = h.index('z')
        
        poses = []
        for row in r:
            row = [c.strip() for c in row]
            if len(row) > z_idx:
                poses.append([float(row[t_idx]), float(row[x_idx]), float(row[y_idx]), float(row[z_idx])])
        poses = np.array(poses)
        
    t = poses[:, 0] - poses[0, 0]
    x = poses[:, 1]
    y = poses[:, 2]
    z = poses[:, 3]
    
    print(f"Total duration: {t[-1]:.1f} s")
    print(f"Trajectory bounds: X in [{x.min():.2f}, {x.max():.2f}], Z in [{z.min():.2f}, {z.max():.2f}]")
    
    # Simple spatial binning / 2D histogram of poses
    H, xedges, zedges = np.histogram2d(x, z, bins=20)
    print("Pose density grid (where the user spent time):")
    for i in range(len(xedges)-1):
        row_str = "".join(["#" if H[i,j] > 10 else "." for j in range(len(zedges)-1)])
        if "#" in row_str:
            print(f"X={xedges[i]:5.1f} | {row_str}")

print("=== Scanning c7d28f72c6 ===")
analyze_rooms_in_scan('data/c7d28f72c6/odometry.csv')
print("\n=== Scanning 1a8384c3f6 ===")
analyze_rooms_in_scan('data/1a8384c3f6/odometry.csv')
print("\n=== Scanning c00a170fe1 ===")
analyze_rooms_in_scan('data/c00a170fe1/odometry.csv')
