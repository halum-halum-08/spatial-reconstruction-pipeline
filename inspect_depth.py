import zipfile
import io
import numpy as np
from PIL import Image

with zipfile.ZipFile('single_room.zip', 'r') as z:
    prefix = 'c00a170fe1'
    depth_files = [f for f in z.namelist() if '/depth/' in f and f.endswith('.png')]
    conf_files = [f for f in z.namelist() if '/confidence/' in f and f.endswith('.png')]
    
    first_d = sorted(depth_files)[0]
    first_c = sorted(conf_files)[0]
    
    img_d = Image.open(io.BytesIO(z.read(first_d)))
    img_c = Image.open(io.BytesIO(z.read(first_c)))
    
    arr_d = np.array(img_d)
    arr_c = np.array(img_c)
    
    print("Depth image:", first_d)
    print("  Mode:", img_d.mode, "Format:", img_d.format, "Size:", img_d.size)
    print("  Dtype:", arr_d.dtype, "Shape:", arr_d.shape)
    print("  Min:", arr_d.min(), "Max:", arr_d.max(), "Mean:", arr_d[arr_d > 0].mean() if np.any(arr_d > 0) else 0)
    print("  Non-zero percentage:", 100.0 * np.count_nonzero(arr_d) / arr_d.size)
    
    print("\nConfidence image:", first_c)
    print("  Mode:", img_c.mode, "Format:", img_c.format, "Size:", img_c.size)
    print("  Dtype:", arr_c.dtype, "Shape:", arr_c.shape)
    print("  Unique values:", np.unique(arr_c))
