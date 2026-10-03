import zipfile
import io
import csv
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation as R

def reconstruct_sample_pointcloud(zip_path, prefix, max_frames=50, step=30):
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Load camera matrix
        cam_text = z.read(f"{prefix}/camera_matrix.csv").decode('utf-8').strip().split('\n')
        K_rgb = np.array([[float(v.strip()) for v in line.split(',') if v.strip()] for line in cam_text])
        # Depth is 256x192, RGB is 1920x1440. Scaling is 1920/256 = 7.5
        scale_x = 1920.0 / 256.0
        scale_y = 1440.0 / 192.0
        fx = K_rgb[0, 0] / scale_x
        fy = K_rgb[1, 1] / scale_y
        cx = K_rgb[0, 2] / scale_x
        cy = K_rgb[1, 2] / scale_y
        
        # Load odometry
        odo_text = z.read(f"{prefix}/odometry.csv").decode('utf-8').strip().split('\n')
        reader = csv.reader(odo_text)
        header = [h.strip() for h in next(reader)]
        frame_idx = header.index('frame')
        x_idx = header.index('x')
        y_idx = header.index('y')
        z_idx = header.index('z')
        qx_idx = header.index('qx')
        qy_idx = header.index('qy')
        qz_idx = header.index('qz')
        qw_idx = header.index('qw')
        
        poses = {}
        for raw_row in reader:
            row = [c.strip() for c in raw_row]
            if not row or len(row) <= qw_idx:
                continue
            fnum = f"{int(row[frame_idx]):06d}"
            pos = np.array([float(row[x_idx]), float(row[y_idx]), float(row[z_idx])])
            quat = [float(row[qx_idx]), float(row[qy_idx]), float(row[qz_idx]), float(row[qw_idx])]
            rot = R.from_quat(quat).as_matrix()
            poses[fnum] = (pos, rot)
            
        all_depth_files = sorted([f for f in z.namelist() if '/depth/' in f and f.endswith('.png')])
        print(f"Total depth frames available: {len(all_depth_files)}")
        
        selected_frames = all_depth_files[::step][:max_frames]
        print(f"Sampling {len(selected_frames)} frames...")
        
        world_pts = []
        u_coords, v_coords = np.meshgrid(np.arange(256), np.arange(192))
        
        for df in selected_frames:
            fnum = df.split('/')[-1].replace('.png', '')
            if fnum not in poses:
                continue
            pos, rot = poses[fnum]
            
            # Read depth & confidence
            depth_img = Image.open(io.BytesIO(z.read(df)))
            depth_arr = np.array(depth_img, dtype=np.float32) / 1000.0 # to meters
            
            cf = df.replace('/depth/', '/confidence/')
            if cf in z.namelist():
                conf_img = Image.open(io.BytesIO(z.read(cf)))
                conf_arr = np.array(conf_img)
                valid = (depth_arr > 0.3) & (depth_arr < 5.0) & (conf_arr >= 1)
            else:
                valid = (depth_arr > 0.3) & (depth_arr < 5.0)
                
            u_valid = u_coords[valid]
            v_valid = v_coords[valid]
            z_valid = depth_arr[valid]
            
            # In camera optical frame: Z forward, X right, Y down
            x_cam = (u_valid - cx) * z_valid / fx
            y_cam = (v_valid - cy) * z_valid / fy
            z_cam = z_valid
            
            cam_pts = np.vstack([x_cam, y_cam, z_cam]) # (3, N)
            
            # Transform to world frame
            # In Stray Scanner / ARKit:
            # rot is camera to world rotation matrix
            # world_pt = rot @ cam_pt + pos
            pts_world = (rot @ cam_pts).T + pos # (N, 3)
            
            # Subsample points
            if len(pts_world) > 1000:
                idx = np.random.choice(len(pts_world), 1000, replace=False)
                world_pts.append(pts_world[idx])
            else:
                world_pts.append(pts_world)
                
        all_pts = np.vstack(world_pts)
        print(f"Total reconstructed points: {len(all_pts)}")
        print(f"Points bounds:")
        print(f"  X: {all_pts[:,0].min():.2f} to {all_pts[:,0].max():.2f}")
        print(f"  Y: {all_pts[:,1].min():.2f} to {all_pts[:,1].max():.2f}")
        print(f"  Z: {all_pts[:,2].min():.2f} to {all_pts[:,2].max():.2f}")
        
        # In this world coordinate system, what are the vertical limits?
        # Let's check percentiles of Y
        y_percentiles = np.percentile(all_pts[:,1], [1, 5, 10, 50, 90, 95, 99])
        print("Y percentiles [1, 5, 10, 50, 90, 95, 99]:", np.round(y_percentiles, 3))
        
        # Check X and Z extents
        print(f"X span: {all_pts[:,0].max() - all_pts[:,0].min():.2f} m")
        print(f"Z span: {all_pts[:,2].max() - all_pts[:,2].min():.2f} m")
        
        return all_pts

print("=== Testing point cloud reconstruction for single_room (c00a170fe1) ===")
pts_single = reconstruct_sample_pointcloud('single_room.zip', 'c00a170fe1', max_frames=40, step=40)
