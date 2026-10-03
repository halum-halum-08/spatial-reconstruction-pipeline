import zipfile
import os

zips = {
    'c00a170fe1': 'single_room.zip',
    '1a8384c3f6': 'single_scan_floor_only.zip',
    'c7d28f72c6': 'single_scan_with_ceiling.zip'
}

os.makedirs('data', exist_ok=True)

for scan_id, zpath in zips.items():
    print(f"Extracting metadata for {scan_id} from {zpath}...")
    scan_dir = os.path.join('data', scan_id)
    os.makedirs(scan_dir, exist_ok=True)
    with zipfile.ZipFile(zpath, 'r') as z:
        for f in z.namelist():
            # Extract csv files and top-level files
            if f.endswith('.csv'):
                base = os.path.basename(f)
                with open(os.path.join(scan_dir, base), 'wb') as out_f:
                    out_f.write(z.read(f))
                print(f"  Extracted {base}")
            elif f.endswith('.mp4'):
                base = os.path.basename(f)
                mp4_path = os.path.join(scan_dir, base)
                if not os.path.exists(mp4_path):
                    with open(mp4_path, 'wb') as out_f:
                        out_f.write(z.read(f))
                    print(f"  Extracted {base}")

print("Metadata extraction complete!")
