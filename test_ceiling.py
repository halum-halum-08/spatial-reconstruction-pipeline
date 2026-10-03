import sys
from reconstruct_test import reconstruct_sample_pointcloud
import numpy as np

print("=== Testing point cloud reconstruction for with_ceiling (c7d28f72c6) ===")
pts_ceiling = reconstruct_sample_pointcloud('single_scan_with_ceiling.zip', 'c7d28f72c6', max_frames=60, step=120)

y_pts = pts_ceiling[:, 1]
# Let's find density peaks in Y (histogram) to locate Floor and Ceiling planes!
hist, bin_edges = np.histogram(y_pts, bins=100)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
peaks = []
for i in range(1, len(hist)-1):
    if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > len(y_pts)*0.01:
        peaks.append((hist[i], bin_centers[i]))

peaks.sort(key=lambda x: x[0], reverse=True)
print("\nProminent horizontal surface (Y) candidates:")
for count, y_val in peaks[:6]:
    print(f"  Y = {y_val:.3f} m (count={count})")

# Lowest prominent plane is floor, highest is ceiling
y_floor = min(p[1] for p in peaks if p[1] < -1.0)
y_ceiling_candidates = [p[1] for p in peaks if p[1] > 0.5]
if y_ceiling_candidates:
    y_ceiling = max(y_ceiling_candidates)
    print(f"\nEstimated Floor Level:   Y = {y_floor:.3f} m")
    print(f"Estimated Ceiling Level: Y = {y_ceiling:.3f} m")
    print(f"Estimated Ceiling Height: H = {y_ceiling - y_floor:.3f} m ({y_ceiling - y_floor:.2f} m)")
