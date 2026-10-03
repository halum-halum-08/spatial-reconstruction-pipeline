import os
import cv2

rooms_ranges = {
    "living_room": (0, 1800),
    "bathroom": (1800, 3600),
    "dining_room": (5000, 7500),
    "hallway_connector": (7500, 9700)
}

cap = cv2.VideoCapture('data/c7d28f72c6/rgb.mp4')
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

base_dir = "benchmark_data/photos"
os.makedirs(base_dir, exist_ok=True)

for room, (start_f, end_f) in rooms_ranges.items():
    room_dir = os.path.join(base_dir, room)
    os.makedirs(room_dir, exist_ok=True)
    step = (end_f - start_f) // 5
    for i in range(5):
        f_idx = start_f + i * step
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if ret:
            out_img = os.path.join(room_dir, f"still_{i+1:02d}.jpg")
            small = cv2.resize(frame, (960, 720))
            cv2.imwrite(out_img, small)

cap.release()
print("Extracted 5 stills per room into benchmark_data/photos/")
