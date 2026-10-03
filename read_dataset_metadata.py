import zipfile
import io
import csv
import json

zips = {
    'single_room': 'single_room.zip',
    'floor_only': 'single_scan_floor_only.zip',
    'with_ceiling': 'single_scan_with_ceiling.zip'
}

for label, zpath in zips.items():
    print(f"\n==================== {label} ({zpath}) ====================")
    with zipfile.ZipFile(zpath, 'r') as z:
        namelist = z.namelist()
        prefix = namelist[0].split('/')[0]
        print(f"Scan ID Prefix: {prefix}")
        print(f"Total files in archive: {len(namelist)}")
        
        # Check files
        for fname in [f"{prefix}/camera_matrix.csv", f"{prefix}/odometry.csv", f"{prefix}/imu.csv"]:
            if fname in namelist:
                data = z.read(fname).decode('utf-8').strip().split('\n')
                print(f"--- {fname} (total lines: {len(data)}) ---")
                for line in data[:5]:
                    print("  ", line)
                if len(data) > 5:
                    print("  ...")
                    print("  ", data[-1])
            else:
                print(f"--- {fname} NOT FOUND ---")
        
        # Check rgb.mp4 size
        rgb_name = f"{prefix}/rgb.mp4"
        if rgb_name in namelist:
            info = z.getinfo(rgb_name)
            print(f"RGB video: {rgb_name}, size: {info.file_size / (1024*1024):.2f} MB")
        
        depth_files = [f for f in namelist if '/depth/' in f and f.endswith('.png')]
        conf_files = [f for f in namelist if '/confidence/' in f and f.endswith('.png')]
        print(f"Depth frames count: {len(depth_files)}")
        print(f"Confidence frames count: {len(conf_files)}")
        if depth_files:
            print(f"Depth range: {depth_files[0]} to {depth_files[-1]}")
