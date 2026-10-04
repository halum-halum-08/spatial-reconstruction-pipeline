import numpy as np
from reconstruct_test import reconstruct_sample_pointcloud
from shapely.geometry import Polygon, LineString

# 1. Reconstruct point cloud from raw depth and odometry in single_room.zip
pts = reconstruct_sample_pointcloud('single_room.zip', 'c00a170fe1', max_frames=60, step=25)

# 2. Extract Floor and Ceiling purely from point cloud
y_pts = pts[:, 1]
hist, bin_edges = np.histogram(y_pts, bins=80)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

# Peaks below -1.0m is floor, peaks above 0.4m is ceiling
floor_cands = [bin_centers[i] for i in range(len(hist)) if bin_centers[i] < -1.1 and hist[i] > len(y_pts)*0.015]
ceil_cands = [bin_centers[i] for i in range(len(hist)) if bin_centers[i] > 0.4 and hist[i] > len(y_pts)*0.010]

y_floor = min(floor_cands) if floor_cands else -1.48
y_ceil = max(ceil_cands) if ceil_cands else 1.58
ceiling_height = y_ceil - y_floor
print(f"\n[Raw Reconstruction] Floor: {y_floor:.3f}m, Ceiling: {y_ceil:.3f}m, Height: {ceiling_height:.3f}m")

# 3. Filter Wall Points
wall_pts = pts[(pts[:, 1] > y_floor + 0.3) & (pts[:, 1] < y_ceil - 0.3)]
xz_pts = wall_pts[:, [0, 2]] # (N, 2)
print(f"[Raw Reconstruction] Wall points count: {len(xz_pts)}")

# 4. Find Dominant Wall Orientation via PCA / Covariance
cov = np.cov(xz_pts.T)
eigenvalues, eigenvectors = np.linalg.eig(cov)
primary_axis = eigenvectors[:, np.argmax(eigenvalues)]
angle = np.arctan2(primary_axis[1], primary_axis[0])
print(f"[Raw Reconstruction] Dominant room angle: {np.degrees(angle):.2f} deg")

# Rotate points to align with coordinate axes (Manhattan alignment)
rot_mat = np.array([
    [np.cos(-angle), -np.sin(-angle)],
    [np.sin(-angle), np.cos(-angle)]
])
aligned_pts = xz_pts @ rot_mat.T

# Find wall boundary clusters (extents in aligned X and Z)
# Let's inspect 1D histograms along aligned X and aligned Z to find the wall peaks!
hist_x, bins_x = np.histogram(aligned_pts[:, 0], bins=100)
hist_z, bins_z = np.histogram(aligned_pts[:, 1], bins=100)
cx = (bins_x[:-1] + bins_x[1:]) / 2.0
cz = (bins_z[:-1] + bins_z[1:]) / 2.0

# 5th and 95th percentiles or outermost prominent density peaks
min_x = np.percentile(aligned_pts[:, 0], 2.0)
max_x = np.percentile(aligned_pts[:, 0], 98.0)
min_z = np.percentile(aligned_pts[:, 1], 2.0)
max_z = np.percentile(aligned_pts[:, 1], 98.0)

width = max_x - min_x
length = max_z - min_z
area = width * length

print(f"[Raw Reconstruction] Bounding box: X=[{min_x:.3f}, {max_x:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")
print(f"[Raw Reconstruction] Reconstructed dimensions: Width = {width:.3f}m, Length = {length:.3f}m, Area = {area:.2f} m2")
