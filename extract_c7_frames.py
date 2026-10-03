import cv2
import os

os.makedirs('extracted_frames_c7', exist_ok=True)
cap = cv2.VideoCapture('data/c7d28f72c6/rgb.mp4')
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Total video frames: {total_frames}, FPS: {fps:.2f}")

for i, frame_idx in enumerate(range(0, total_frames, max(1, total_frames // 12))):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        out_path = f"extracted_frames_c7/frame_{i:02d}_{frame_idx:04d}.jpg"
        small = cv2.resize(frame, (640, 480))
        cv2.imwrite(out_path, small)

cap.release()
print("Saved 12 frames from c7d28f72c6")
