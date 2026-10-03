import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reconstruct_test import reconstruct_sample_pointcloud

pts = reconstruct_sample_pointcloud('single_room.zip', 'c00a170fe1', max_frames=80, step=20)

# Filter out floor and ceiling points to keep only wall and obstacle points
# Floor is at -1.48, ceiling is at +1.58
# Wall points are between -1.0 and +0.4
wall_mask = (pts[:, 1] > -1.1) & (pts[:, 1] < 0.4)
wall_pts = pts[wall_mask]

print(f"Wall points count: {len(wall_pts)}")

# 2D projection onto (X, Z)
plt.figure(figsize=(10, 10))
plt.scatter(wall_pts[:, 0], wall_pts[:, 2], s=1, alpha=0.3, c='blue')
plt.title("Single Room 2D Point Cloud (X vs Z)")
plt.xlabel("X (meters)")
plt.ylabel("Z (meters)")
plt.grid(True)
plt.axis('equal')
plt.savefig("room_walls_2d.png", dpi=150)
print("Saved room_walls_2d.png")
