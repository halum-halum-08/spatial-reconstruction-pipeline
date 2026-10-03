import os
import zipfile

zip_filename = "spatial_pipeline_submission.zip"
include_dirs = ["pipeline", "tiers", "scripts", "benchmark_data", "fix_loop", "outputs"]
include_files = [
    "README.md",
    "COMPLIANCE_MATRIX.md",
    "CAPTURE_ROUTE.md",
    "DEVICE_MATRIX.md",
    "BENCHMARK_REPORT.md",
    "FIX_DECLARATION.md",
    "TECHNICAL_REPORT.md",
    ".gitignore"
]

MAX_FILE_SIZE = 1 * 1024 * 1024 # 1 MB limit per file

total_files = 0
total_uncompressed_bytes = 0
skipped_files = []

with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
    # Add root files
    for f in include_files:
        if os.path.exists(f):
            sz = os.path.getsize(f)
            if sz > MAX_FILE_SIZE:
                skipped_files.append((f, sz))
                print(f"[!] Dropping {f} (size: {sz/1024/1024:.2f} MB > 1 MB)")
            else:
                zf.write(f, arcname=f)
                total_files += 1
                total_uncompressed_bytes += sz
                print(f"  [+] Added file: {f} ({sz/1024:.1f} KB)")

    # Add directories
    for d in include_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            # Exclude __pycache__
            dirs[:] = [sub for sub in dirs if sub != "__pycache__"]
            for file in sorted(files):
                if file.endswith(('.pyc', '.pyo')):
                    continue
                full_path = os.path.join(root, file)
                sz = os.path.getsize(full_path)
                if sz > MAX_FILE_SIZE:
                    skipped_files.append((full_path, sz))
                    print(f"[!] Dropping {full_path} (size: {sz/1024/1024:.2f} MB > 1 MB)")
                else:
                    arcname = os.path.relpath(full_path, ".")
                    zf.write(full_path, arcname=arcname)
                    total_files += 1
                    total_uncompressed_bytes += sz

zip_size = os.path.getsize(zip_filename)
print("\n" + "="*60)
print(f"ZIP ARCHIVE CREATED: {zip_filename}")
print(f"Total files packed: {total_files}")
print(f"Total uncompressed size: {total_uncompressed_bytes / 1024:.1f} KB ({total_uncompressed_bytes/1024/1024:.2f} MB)")
print(f"Compressed archive size: {zip_size / 1024:.1f} KB ({zip_size/1024/1024:.2f} MB)")
print(f"Files dropped (> 1 MB): {len(skipped_files)}")
print("="*60)
