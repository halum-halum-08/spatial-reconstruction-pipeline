# CAPTURE ROUTE & STOCK CAPTURE PROTOCOL

**Protocol Designation:** Field Operator Standard Operating Procedure (SOP-CAP-2026)  
**Target Audience:** Non-engineer field technicians, claims adjusters, and homeowners  
**Equipment Permitted:** Any iPhone 15, iPhone 15 Pro, iPhone 16, or newer iOS device  

---

### Step 1: What to Install (Setup Time: < 3 Minutes)

Depending on your assigned hardware tier, install the following free, off-the-shelf software from the Apple App Store:

1. **For LiDAR Tier (Pro-Class Devices — iPhone 15 Pro / 16 Pro or newer):**
   * Open the App Store and search for **"Stray Scanner"** (free, open-source LiDAR and visual-inertial logger) or **"Record3D"**.
   * Tap **Get / Install**.
   * Launch the app and grant permissions for **Camera**, **Motion & Sensors**, and **Local Network / Files**.
   * In Settings, ensure **Format: ARKit Depth + 6-DoF Odometry** is selected (default).
2. **For Video Tier (Base Devices — Standard iPhone 15 / 16 or newer):**
   * Use the **Native iOS Camera App** (pre-installed).
   * Go to **iOS Settings $\rightarrow$ Camera $\rightarrow$ Record Video** and select **1080p at 30 fps** or **4K at 30 fps**.
3. **For Photo Tier (Any iPhone 15 or newer):**
   * Use the **Native iOS Camera App**. Ensure photo resolution is set to standard 12MP or 24MP.

---

### Step 2: How to Walk the Property (The "Perimeter Loop" Pattern)

1. **Starting Point:**
   * Stand in the main entryway or primary doorway of the property.
   * Hold the phone upright in two hands at chest height (approximately 1.3 m – 1.5 m from the ground), tilted slightly downward ($\approx 15^\circ$) so the floor plane and lower walls remain clearly visible.
2. **Walking Cadence & Speed:**
   * Walk at a continuous, steady pace of **0.5 to 0.8 meters per second** (a calm, deliberate walking pace).
   * **Do NOT run, jog, or make sudden jerky turns.** Turn your entire body smoothly rather than pivoting the phone on your wrist.
3. **The Loop Pattern:**
   * Trace the outer perimeter of each room in a clockwise direction.
   * As you walk along each wall, gently pitch the phone upward once per wall to capture the wall-ceiling junction, then return to eye level.
   * Walk through connecting hallways into adjacent rooms in a single continuous path.
4. **Mandatory Loop Closure:**
   * **You MUST finish the walkthrough in the exact spot and orientation where you started.** Return to the entryway and point the phone at the initial starting wall for 2 seconds before pressing Stop. This enables our backend drift correction engine to execute zero-residual loop closure.

---

### Step 3: Duration & Scan Sizing

* **Single Room:** 30 to 45 seconds (approximately 15–20 meters of walking path).
* **Multi-Room Suite (3–4 rooms + connector):** 2.5 to 4 minutes (approximately 60–100 meters of walking path).
* **Sparse Photo Tier:** Take **4 to 6 photos per room**: one photo standing at each corner facing the opposite diagonal, plus one overview photo of any interior opening/doorway.

---

### Step 4: Environmental Conditions & What to Avoid

* **Lighting:** Turn ON all overhead ceiling lights and room lamps before scanning. Open blinds if room is dim. Avoid total darkness.
* **Mirrors & Glass Partitions:** Keep the phone tilted slightly away from direct normal reflection to avoid specular glare. Our pipeline's dual-boundary filter handles reflection dropouts, but avoid pausing directly in front of large mirrors.
* **Doors:** Ensure all interior doors connecting rooms are propped **fully open ($90^\circ$ or wider)** before beginning the walk. Do NOT open or close doors mid-scan.
* **Obstacles:** Walk around furniture smoothly. Do not climb over obstacles.

---

### Step 5: How to Hand the Files to the Pipeline

1. **LiDAR Tier:**
   * In Stray Scanner, tap on the completed scan and tap **Share $\rightarrow$ Save to Files** (or AirDrop to your computer).
   * The scan exports as a `.zip` archive (e.g., `capture_with_ceiling.zip`) containing `odometry.csv`, `camera_matrix.csv`, `depth/`, and `rgb.mp4`.
2. **Video Tier:**
   * AirDrop or export the recorded walkthrough `.mp4` / `.mov` file to your computer.
3. **Photo Tier:**
   * Create one folder per room (e.g., `living_room/`, `bathroom/`, `dining_room/`, `hallway/`) and place that room's stills into its respective folder.
4. **Run the Pipeline:**
   Execute the single CLI command on your computer:
   ```bash
   # LiDAR Tier:
   python scripts/run_capture.py --input capture_with_ceiling.zip

   # Video Tier:
   python scripts/run_capture.py --input walkthrough_video.mp4

   # Photo Tier:
   python scripts/run_capture.py --input photos_folder/
   ```
