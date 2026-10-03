import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reconstruct_test import reconstruct_sample_pointcloud

pts = reconstruct_sample_pointcloud('single_scan_with_ceiling.zip', 'c7d28f72c6', max_frames=120, step=80)

wall_mask = (pts[:, 1] > -1.1) & (pts[:, 1] < 0.4)
wall_pts = pts[wall_mask]

print(f"Wall points count: {len(wall_pts)}")

plt.figure(figsize=(12, 12))
plt.scatter(wall_pts[:, 0], wall_pts[:, 2], s=1, alpha=0.25, c='darkblue')
plt.title("Multi-Room Scan 2D Point Cloud (c7d28f72c6)")
plt.xlabel("X (meters)")
plt.ylabel("Z (meters)")
plt.grid(True)
plt.axis('equal')
plt.savefig("multi_room_2d.png", dpi=150)
print("Saved multi_room_2d.png")
