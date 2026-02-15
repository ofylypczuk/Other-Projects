import cv2
import mediapipe as mp
import numpy as np
import math
import time
import random

# Fix for some MediaPipe installations where mp.solutions is not auto-imported
try:
    from mediapipe.python import solutions as mp_solutions
    print("Imported solutions from mediapipe.python")
except ImportError:
    try:
        import mediapipe.solutions as mp_solutions
        print("Imported mediapipe.solutions")
    except ImportError:
        if hasattr(mp, 'solutions'):
            mp_solutions = mp.solutions
        else:
            print("CRITICAL WARNING: Could not find mediapipe.solutions!")
            mp_solutions = None


# --- CONFIGURATION ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
ACCENT_COLOR = (0, 255, 255) # Cyan
SECONDARY_COLOR = (255, 0, 255) # Magenta
TEXT_COLOR = (200, 255, 200)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.life = 1.0 # 1.0 to 0.0
        self.color = color
        self.decay = random.uniform(0.05, 0.1)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0

    def draw(self, img):
        alpha = max(0, self.life)
        # Simulate glowing particle
        cv2.circle(img, (int(self.x), int(self.y)), 2, self.color, -1)

class Smoother:
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.value = None

    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=10, color=(255, 255, 255)):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update_and_draw(self, img):
        # Update
        self.particles = [p for p in self.particles if p.update()]
        # Draw
        for p in self.particles:
            p.draw(img)

class SciFiRenderer:
    @staticmethod
    def draw_grid(img):
        h, w, c = img.shape
        # Draw a perspective grid at the bottom
        gap = 100
        color = (50, 50, 0) # Dark Cyan
        for x in range(0, w, gap):
            cv2.line(img, (x, 0), (x, h), color, 1)
        for y in range(0, h, gap):
            cv2.line(img, (0, y), (w, y), color, 1)

    @staticmethod
    def draw_hand_box(img, landmarks):
        # Draw a constant Sci-Fi bracket around the hand
        h, w, c = img.shape
        x_min, y_min = w, h
        x_max, y_max = 0, 0
        for lm in landmarks:
             cx, cy = int(lm.x * w), int(lm.y * h)
             if cx < x_min: x_min = cx
             if cx > x_max: x_max = cx
             if cy < y_min: y_min = cy
             if cy > y_max: y_max = cy
        
        # Expand slightly
        pad = 20
        x_min = max(0, x_min - pad)
        y_min = max(0, y_min - pad)
        x_max = min(w, x_max + pad)
        y_max = min(h, y_max + pad)
        
        # Draw Brackets
        color = (255, 255, 255)
        # Top-Left
        cv2.line(img, (x_min, y_min), (x_min + 30, y_min), color, 2)
        cv2.line(img, (x_min, y_min), (x_min, y_min + 30), color, 2)
        # Bottom-Right
        cv2.line(img, (x_max, y_max), (x_max - 30, y_max), color, 2)
        cv2.line(img, (x_max, y_max), (x_max, y_max - 30), color, 2)

    @staticmethod
    def draw_hand_skeleton(img, landmarks):
        # MediaPipe Tasks API returns NormalizedLandmark objects
        # We need to manually define connections since we lost mp.solutions.hands.HAND_CONNECTIONS
        HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20),
            (0, 17)
        ]
        
        # Convert landmarks to dict for easy access
        lm_dict = {}
        for idx, lm in enumerate(landmarks):
            h, w, c = img.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            lm_dict[idx] = (cx, cy)

        # Draw Glowing Connections
        for p1_id, p2_id in HAND_CONNECTIONS:
            if p1_id in lm_dict and p2_id in lm_dict:
                pt1 = lm_dict[p1_id]
                pt2 = lm_dict[p2_id]
                
                # Outer Glow
                cv2.line(img, pt1, pt2, (0, 100, 100), 5) 
                # Inner Core
                cv2.line(img, pt1, pt2, ACCENT_COLOR, 2)

        # Draw Nodes
        for id, (cx, cy) in lm_dict.items():
            run_color = SECONDARY_COLOR if id in [4, 8, 12, 16, 20] else ACCENT_COLOR
            cv2.circle(img, (cx, cy), 4, run_color, -1)
            cv2.circle(img, (cx, cy), 6, (255, 255, 255), 1)

class HandTracker:
    def __init__(self, model_path='hand_landmarker.task', max_hands=2):
        self.timestamp_ms = 0
        self.results = None
        
        try:
            BaseOptions = mp.tasks.BaseOptions
            HandLandmarker = mp.tasks.vision.HandLandmarker
            HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode

            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=VisionRunningMode.VIDEO,
                num_hands=max_hands,
                min_hand_detection_confidence=0.3, # Highly Sensitive
                min_hand_presence_confidence=0.3, 
                min_tracking_confidence=0.3)
            
            self.landmarker = HandLandmarker.create_from_options(options)
            print("Successfully initialized MediaPipe Tasks API")
        except Exception as e:
            print(f"Failed to initialize MediaPipe Tasks: {e}")
            raise e

    def find_hands(self, img, timestamp_ms):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        self.results = self.landmarker.detect_for_video(mp_image, int(timestamp_ms))
        return self.results

    def get_all_hands_positions(self, img):
        all_hands = []
        if self.results and self.results.hand_landmarks:
            for i, hand_lms in enumerate(self.results.hand_landmarks):
                lm_list = []
                for id, lm in enumerate(hand_lms):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                
                # Get Handedness (Left/Right)
                label = "Unknown"
                if self.results.handedness and len(self.results.handedness) > i:
                    label = self.results.handedness[i][0].category_name
                
                all_hands.append((lm_list, label))
        return all_hands


class LiquidParticle:
    def __init__(self, x, y, z, color):
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.vz = random.uniform(-2, 2)
        self.color = color

class VirtualObject:
    def __init__(self, x, y, size, text, color):
        self.x = x
        self.y = y
        self.z = 0 
        self.size = size
        self.text = text
        self.base_color = (255, 255, 255) # White Wireframe
        self.liquid_color = (0, 0, 255)   # Red Liquid (BGR)
        self.current_color = self.base_color
        
        # Physics (Position)
        self.vx = 0
        self.vy = 0
        self.last_x = x
        self.last_y = y
        self.friction = 0.92
        self.interaction_active = False 
        
        # 3D Transforms
        self.scale = 1.0
        self.rotation = 0.0 
        # Fixed 3D Perspective (Isometric-ish) - STABLE
        self.rot_x = 0.5 
        self.rot_y = 0.5 
        
        # Particle Liquid System
        self.particles = []
        self.num_particles = 600 # "Millions" (Simulated)
        for _ in range(self.num_particles):
             # Spawn randomly inside LOWER HALF
             s = self.size * 0.4 
             self.particles.append(LiquidParticle(
                 random.uniform(-s, s),
                 random.uniform(0, s), # Lower half (y > 0 is down in screen, but local space?)
                                       # Let's assume Local 0,0,0 is center. Y+ is down?
                                       # If we want "half filled", liquid settles at bottom.
                                       # In local space, let's fill -s to s?
                                       # Gravity pulls to +Y in World.
                                       # So "Bottom" is +Y.
                                       # Spawn in [0, s] (Bottom half)
                 random.uniform(-s, s),
                 self.liquid_color
             ))

    def update(self, bounds_w, bounds_h):
        # 1. Position Physics
        if not self.interaction_active:
            self.x += self.vx
            self.y += self.vy
            self.vx *= self.friction
            self.vy *= self.friction
            
            if abs(self.vx) < 0.1: self.vx = 0
            if abs(self.vy) < 0.1: self.vy = 0

            # Bounce
            s = self.size * self.scale * 0.5
            if self.x - s < 0: self.x, self.vx = s, -self.vx * 0.6
            elif self.x + s > bounds_w: self.x, self.vx = bounds_w - s, -self.vx * 0.6
            if self.y - s < 0: self.y, self.vy = s, -self.vy * 0.6
            elif self.y + s > bounds_h: self.y, self.vy = bounds_h - s, -self.vy * 0.6
            
        else:
             self.vx = (self.x - self.last_x)
             self.vy = (self.y - self.last_y)
             self.last_x = self.x
             self.last_y = self.y
             self.current_color = (255, 255, 255)

        if not self.interaction_active:
            self.current_color = self.base_color

        # 2. Particle Physics
        # Move particles relative to cube center
        # Forces: Gravity (down world space), Inertia (opposing accel)
        
        # Build Rotation Matrix (same as draw)
        # Use FIXED rot_x/y and dynamic rotation (Z)
        cx, sx = math.cos(self.rot_x), math.sin(self.rot_x)
        cy, sy = math.cos(self.rot_y), math.sin(self.rot_y)
        cz, sz = math.cos(self.rotation), math.sin(self.rotation) 
        
        # R = Rz * Ry * Rx
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx
        R_inv = R.T 
        
        # World Forces
        gravity_world = np.array([0.0, 0.8, 0.0]) # Stronger Gravity
        accel_world = np.array([self.vx * 0.2, self.vy * 0.2, 0.0])
        force_world = gravity_world - accel_world
        
        # Transform force to Local Space
        force_local = R_inv @ force_world
        
        limit = self.size * 0.45 * self.scale
        
        for p in self.particles:
            # Apply force
            p.vx += force_local[0] + random.uniform(-0.05, 0.05)
            p.vy += force_local[1] + random.uniform(-0.05, 0.05)
            p.vz += force_local[2] + random.uniform(-0.05, 0.05)
            
            # Dampen
            p.vx *= 0.90
            p.vy *= 0.90
            p.vz *= 0.90
            
            p.x += p.vx
            p.y += p.vy
            p.z += p.vz
            
            # Bounds Check (Cube Box)
            if p.x < -limit: p.x, p.vx = -limit, -p.vx * 0.5
            if p.x > limit: p.x, p.vx = limit, -p.vx * 0.5
            if p.y < -limit: p.y, p.vy = -limit, -p.vy * 0.5
            if p.y > limit: p.y, p.vy = limit, -p.vy * 0.5
            if p.z < -limit: p.z, p.vz = -limit, -p.vz * 0.5
            if p.z > limit: p.z, p.vz = limit, -p.vz * 0.5


    def draw(self, img):
        # Define Cube Vertices (Local Space)
        s = self.size * self.scale * 0.5
        vertices = np.array([
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s], # Front Face
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]      # Back Face
        ])
        
        # NO PHYSICS TILT - STABLE
        # Fixed Perspective + User Z-Rotation
        
        # Rotation Matrices
        cx, sx = math.cos(self.rot_x), math.sin(self.rot_x)
        cy, sy = math.cos(self.rot_y), math.sin(self.rot_y)
        cz, sz = math.cos(self.rotation), math.sin(self.rotation) 
        
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx
        
        # Project Vertices
        screen_points = []
        for v in vertices:
            rv = R @ v
            z_cam = 600
            factor = z_cam / (z_cam + rv[2])
            px = int(self.x + rv[0] * factor)
            py = int(self.y + rv[1] * factor)
            screen_points.append((px, py))
            
        # Draw Particles (Projected)
        for p in self.particles:
            # Rotate particle pos
            pv = np.array([p.x, p.y, p.z])
            rp = R @ pv
            
            # Project
            z_cam = 600
            factor = z_cam / (z_cam + rp[2])
            px = int(self.x + rp[0] * factor)
            py = int(self.y + rp[1] * factor)
            
            # Draw (Red Dot)
            h, w = img.shape[:2]
            if 0 < px < w and 0 < py < h:
                 # Depth Cuing?
                 radius = 2 if rp[2] < 0 else 3
                 cv2.circle(img, (px, py), radius, (0, 0, 255), -1)

        # Draw Wireframe (White)
        edges = [
            (0,1), (1,2), (2,3), (3,0), # Front
            (4,5), (5,6), (6,7), (7,4), # Back
            (0,4), (1,5), (2,6), (3,7)  # Connecting
        ]
        
        for i, j in edges:
            pt1 = screen_points[i]
            pt2 = screen_points[j]
            cv2.line(img, pt1, pt2, self.current_color, 2)
            
        # Draw Connectors
        for pt in screen_points:
             cv2.circle(img, pt, 3, (255, 255, 255), -1)

    def contains(self, px, py):
        s = self.size * self.scale * 0.7 
        return math.hypot(px - self.x, py - self.y) < s

class WorkspaceApp:
    def __init__(self, bounds_w=WINDOW_WIDTH, bounds_h=WINDOW_HEIGHT):
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(3, WINDOW_WIDTH)
            self.cap.set(4, WINDOW_HEIGHT)
        except Exception as e:
            print(f"Error opening camera: {e}")
            exit()
            
        # Using Tasks API now
        self.tracker = HandTracker(max_hands=2)
        
        self.objects = [
            VirtualObject(300, 300, 150, "SYSTEM", (200, 100, 0)),
            VirtualObject(900, 400, 150, "BLUEPRINT", (0, 200, 50)),
            VirtualObject(600, 200, 100, "LOGS", (200, 0, 200))
        ]
        self.particles = ParticleSystem()
        
        self.active_object = None
        self.interaction_mode = 'IDLE' 
        self.debug_img = None
        self.start_dist = 0
        self.start_angle = 0
        self.start_obj_scale = 1.0
        self.start_obj_rot = 0.0
        
        # Stabilization
        self.hand_smoothers = {} # Map id -> (SmootherX, SmootherY)

    def get_smoothed_hand(self, hand_id, x, y):
        if hand_id not in self.hand_smoothers:
            self.hand_smoothers[hand_id] = (Smoother(0.8), Smoother(0.8))
        
        sx, sy = self.hand_smoothers[hand_id]
        return int(sx.update(x)), int(sy.update(y))

    def run(self):
        pTime = 0
        start_time = time.time() * 1000
        
        while True:
            success, img = self.cap.read()
            if not success:
                print("Failed to read camera frame.")
                break
            
            img = cv2.flip(img, 1)
            h, w, c = img.shape
            self.debug_img = img # IMPORTANT: Allow process_interaction to draw debug info
            
            # --- Tracking (Tasks API) ---
            timestamp_ms = (time.time() * 1000) - start_time
            self.tracker.find_hands(img, timestamp_ms)
            
            # --- Logic ---
            hands_data = self.tracker.get_all_hands_positions(img)
            self.process_interaction(hands_data, w, h)
            
            # Update Objects
            for obj in self.objects:
                obj.update(w, h)
            
            # --- Rendering ---
            for obj in self.objects:
                obj.draw(img)
            self.particles.update_and_draw(img)
            
            # Draw Hands
            # Since get_all_hands_positions returns exactly what we need (list of lm_list)
            # We can use that for drawing too.
            # But the Tasks API returns normalized landmarks in results.
            # We already converted them in get_all_hands_positions, but NOT as Landmark objects.
            # The custom renderer expects a list of points or landmarks with .x .y?
            # Wait, our new SciFiRenderer.draw_hand_skeleton expects landmarks with .x .y attributes!
            # BUT get_all_hands_positions returns [[id, cx, cy], ...]
            # SciFiRenderer.draw_hand_skeleton expects objects with .x and .y attributes (from previous implementation).
            # We need to fix this.
            
            # if self.tracker.results and self.tracker.results.hand_landmarks:
            #     for hand_lms in self.tracker.results.hand_landmarks:
            #         SciFiRenderer.draw_hand_skeleton(img, hand_lms)
            #         SciFiRenderer.draw_hand_box(img, hand_lms)
                
            # HUD
            cTime = time.time()
            fps = 1 / (cTime - pTime) if pTime > 0 else 0
            pTime = cTime
            self.draw_hud(img, fps, hands_data)
            
            cv2.imshow("Holographic AR Workspace", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()

    def process_interaction(self, hands, w, h):
        pinching_hands = []
        
        self.interaction_info = "NONE" # Debug info for HUD

        for hand_data in hands:
            lm_list = hand_data[0]
            label = hand_data[1] # "Left" or "Right"

            # Coordinates
            x4, y4 = lm_list[4][1], lm_list[4][2] # Thumb Tip
            x8, y8 = lm_list[8][1], lm_list[8][2] # Index Tip
            
            # --- Visual Debug: Draw Line between Thumb and Index ---
            # cv2.line(self.debug_img, (x4, y4), (x8, y8), (100, 100, 100), 1)
            # Draw Hand Label
            # cv2.putText(self.debug_img, label, (x8, y8-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 200), 1)

            length = math.hypot(x8-x4, y8-y4)
            
            # Hysteresis Logic
            # If already grabbing (active object exists and is interaction active), detection is easier (release threshold)
            # If not grabbing, detection is harder (grab threshold)
            
            is_grabbing_now = False
            if self.active_object and self.active_object.interaction_active and self.interaction_mode == 'GRAB':
                 if length < 80: # Release Interval (Keep holding until 80px)
                     is_grabbing_now = True
            else:
                 if length < 40: # Grab Interval (Start holding at 40px)
                     is_grabbing_now = True

            if is_grabbing_now:
                # Apply Smoothing to the interaction point
                cx, cy = (x8 + x4)//2, (y8 + y4)//2
                sx, sy = self.get_smoothed_hand(label, cx, cy) # KEY FIX: Use label, not index 'i'
                
                pinching_hands.append((label, sx, sy))
                # cv2.circle(self.debug_img, (sx, sy), 10, (0, 255, 0), -1) # Green marker for pinch
                
        # --- STATE MACHINE ---
        
        # 1. Bimanual (Two Pinches)
        if len(pinching_hands) == 2:
            prev_mode = self.interaction_mode
            self.interaction_mode = 'BIMANUAL_SCALE_ROT'
            h1 = pinching_hands[0]
            h2 = pinching_hands[1]
            cw, ch = (h1[1] + h2[1]) // 2, (h1[2] + h2[2]) // 2
            
            # If we just switched from GRAB to BIMANUAL, we MUST reset the start parameters!
            # Or if we just started fresh
            need_init = (prev_mode != 'BIMANUAL_SCALE_ROT')

            if need_init or not self.active_object:
               # Find or re-bind object
               target_obj = self.active_object
               if not target_obj:
                   for obj in self.objects:
                       if obj.contains(cw, ch):
                           target_obj = obj
                           break
               
               if target_obj:
                   self.active_object = target_obj
                   self.active_object.interaction_active = True
                   
                   # Init Parameters
                   self.start_dist = math.hypot(h1[1]-h2[1], h1[2]-h2[2])
                   self.start_angle = math.atan2(h1[2]-h2[2], h1[1]-h2[1])
                   self.start_cx = cw
                   self.start_cy = ch
                   
                   self.start_obj_scale = target_obj.scale
                   self.start_obj_rot = target_obj.rotation
                   self.start_obj_rot_x = target_obj.rot_x
                   self.start_obj_rot_y = target_obj.rot_y
                   
                   self.particles.emit(cw, ch, 20, (255, 255, 0)) # Sparks
                   
                   # Reset Smoothers for Bimanual - VERY SMOOTH (0.1)
                   self.bm_sm_dist = Smoother(0.1)
                   self.bm_sm_angle = Smoother(0.1)
                   self.bm_sm_cx = Smoother(0.1) # New smoothers for X/Y
                   self.bm_sm_cy = Smoother(0.1)
                   
                   # Seed with current values
                   self.bm_sm_dist.update(self.start_dist)
                   self.bm_sm_angle.update(self.start_angle)
                   self.bm_sm_cx.update(cw)
                   self.bm_sm_cy.update(ch)

            if self.active_object:
                # Calculate Raw
                raw_dist = math.hypot(h1[1]-h2[1], h1[2]-h2[2])
                raw_angle = math.atan2(h1[2]-h2[2], h1[1]-h2[1])
                
                # Constraint: Ignore updates if hands are too close (jitter)
                if raw_dist < 60: 
                    return # Skip updates if hands are too close

                # Smooth
                if not hasattr(self, 'bm_sm_dist'): 
                    self.bm_sm_dist = Smoother(0.1)
                    self.bm_sm_angle = Smoother(0.1)
                    self.bm_sm_cx = Smoother(0.1)
                    self.bm_sm_cy = Smoother(0.1)
                    
                curr_dist = self.bm_sm_dist.update(raw_dist)
                curr_angle = self.bm_sm_angle.update(raw_angle)
                curr_cx = self.bm_sm_cx.update(cw)
                curr_cy = self.bm_sm_cy.update(ch)
                
                # 1. Scale
                dist_ratio = curr_dist / (self.start_dist + 1e-5)
                self.active_object.scale = max(0.2, min(5.0, self.start_obj_scale * dist_ratio))
                
                # 2. Rotate Z (Roll) - From Twist
                angle_diff = math.degrees(curr_angle - self.start_angle)
                if abs(angle_diff) > 2.0:
                    self.active_object.rotation = self.start_obj_rot + (curr_angle - self.start_angle)
                
                # 3. Rotate X/Y (Pitch/Yaw) - From Centroid Movement
                # Moving Hands horizontally -> Yaw (Rot Y)
                # Moving Hands vertically -> Pitch (Rot X)
                dx = curr_cx - self.start_cx
                dy = curr_cy - self.start_cy
                
                # Sensitivity
                rot_speed = 0.01
                self.active_object.rot_y = self.start_obj_rot_y + (dx * rot_speed)
                self.active_object.rot_x = self.start_obj_rot_x + (dy * rot_speed) 
                
                # IMPORTANT: Do NOT update active_object.x or y. Position is LOCKED.
                # self.active_object.x = cw
                # self.active_object.y = ch

        # 2. Grab (One Pinch)
        elif len(pinching_hands) == 1:
            self.interaction_mode = 'GRAB'
            h1 = pinching_hands[0]
            cx, cy = h1[1], h1[2]
            
            if not self.active_object:
                # IMPORTANT: Object check needs to happen even if not previously active
                # Check distances to all objects
                for obj in self.objects:
                    if obj.contains(cx, cy):
                        self.active_object = obj
                        self.active_object.interaction_active = True
                        self.particles.emit(cx, cy, 10, (100, 255, 255))
                        break
            
            if self.active_object:
                # Ensure ONLY x, y are updated in GRAB mode
                self.active_object.x = cx
                self.active_object.y = cy
        
        else:
            self.interaction_mode = 'IDLE'
            if self.active_object:
                self.active_object.interaction_active = False
                self.active_object = None
            
            # Hover Feedback
            # If hand is open and over an object, highlight it
            for hand_data in hands:
                # Use mean hand position
                lm_list = hand_data[0] # The list of points
                hx, hy = lm_list[9][1], lm_list[9][2] 
                
                for obj in self.objects:
                    if obj.contains(hx, hy):
                         obj.current_color = (255, 255, 255) # White Glow
                         cv2.putText(self.debug_img, "GRAB NOW", (hx, hy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    def draw_hud(self, img, fps, hands):
        h, w, c = img.shape
        
        # Header
        cv2.rectangle(img, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.line(img, (0, 60), (w, 60), ACCENT_COLOR, 2)
        
        # Stats
        cv2.putText(img, f"FPS: {int(fps)}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ACCENT_COLOR, 2)
        cv2.putText(img, f"STATUS: {self.interaction_mode}", (200, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
         # Hand Targets
        for hand_data in hands:
            lm_list = hand_data[0]
            # Thumb and Index (Pinch targets)
            x4, y4 = lm_list[4][1], lm_list[4][2]
            x8, y8 = lm_list[8][1], lm_list[8][2]
            
            # Draw distance
            dist = math.hypot(x8-x4, y8-y4)
            mid_x, mid_y = (x4+x8)//2, (y4+y8)//2
            
            cv2.putText(img, f"{int(dist)}", (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

            # Target Lock on fingertips
            tips = [4, 8, 12, 16, 20]
            for tip in tips:
                tx, ty = lm_list[tip][1], lm_list[tip][2]
                cv2.line(img, (tx-5, ty), (tx+5, ty), ACCENT_COLOR, 1)
                cv2.line(img, (tx, ty-5), (tx, ty+5), ACCENT_COLOR, 1)

if __name__ == "__main__":
    app = WorkspaceApp()
    app.run()
