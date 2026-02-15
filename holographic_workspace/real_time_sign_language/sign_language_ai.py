import cv2
import mediapipe as mp
import math
import numpy as np
import time
import os
import urllib.request
import threading
from collections import deque
from enum import Enum

# --- INSTALLATION: matches standard libraries + mediapipe opencv-python ---

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = "hand_landmarker.task"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading model from {MODEL_URL}...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading model: {e}")

# --- HAND CONNECTIONS ---
HAND_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 13), (13, 17), (0, 17),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20)
])

# --- ENUMS & CLASSIFIER ---
class FingerState(Enum):
    BENT = 1
    STRAIGHT = 2

class SignClassifier:
    def __init__(self):
        self.buffer_size = 5
        self.history = deque(maxlen=self.buffer_size)

    def get_angle(self, a, b, c):
        """ Calculate angle between three points (a-b-c). """
        # Vectors
        ba = np.array([a.x - b.x, a.y - b.y])
        bc = np.array([c.x - b.x, c.y - b.y])
        
        # Normalize
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        
        if norm_ba == 0 or norm_bc == 0: return 0.0
        
        cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)

    def analyze_hand(self, landmarks):
        """ Returns a dict of finger states based on angles. """
        l = landmarks
        # MediaPipe Indices
        # Thumb: 1-2-3-4
        # Index: 5-6-7-8
        # Middle: 9-10-11-12
        # Ring: 13-14-15-16
        # Pinky: 17-18-19-20
        
        fingers = {}
        
        # 1. Check Folds (Angles at PIP joint)
        # 180 = Straight, 45 = Closed
        # Indices for [MCP, PIP, DIP]
        idx_joints = {
            'index': [5, 6, 7],
            'middle': [9, 10, 11],
            'ring': [13, 14, 15],
            'pinky': [17, 18, 19]
        }
        
        for name, joints in idx_joints.items():
            angle = self.get_angle(l[joints[0]], l[joints[1]], l[joints[2]])
            fingers[name] = angle > 150 # True if straight
            
        # 2. Thumb Logic (Complex)
        # Angle at IP joint (2-3-4)
        thumb_angle = self.get_angle(l[2], l[3], l[4])
        # Also check if it's "tucked" (Tip close to Pinky MCP) or "out"
        # thumb_out = horizontal distance from index base?
        
        fingers['thumb'] = thumb_angle > 150 # Straightish
        
        # 3. Contact Checks (Crucial for letters)
        def dist(i1, i2): 
            return math.hypot(l[i1].x - l[i2].x, l[i1].y - l[i2].y)
            
        fingers['thumb_index_touch'] = dist(4, 8) < 0.05
        fingers['thumb_middle_touch'] = dist(4, 12) < 0.05
        fingers['index_middle_touch'] = dist(8, 12) < 0.04
        
        return fingers

    def classify(self, landmarks):
        f = self.analyze_hand(landmarks)
        
        t = f['thumb']
        i = f['index']
        m = f['middle']
        r = f['ring']
        p = f['pinky']
        
        # Contacts
        ti_touch = f['thumb_index_touch']
        tm_touch = f['thumb_middle_touch']
        
        # --- ALPHABET HEURISTICS (A-Z) ---
        
        # A: All closed, thumb straight up (or side)
        if not i and not m and not r and not p and t:
            return "A"
            
        # B: 4 Open, Thumb Tucked (Bent)
        if i and m and r and p and not t:
            return "B"
            
        # C: All curved (Hand creates C shape - angles are ~90-120, not straight > 150)
        # (This binary Straight/Bent logic might miss C, usually C implies all fingers 'Bent')
        if not i and not m and not r and not p and not t:
            # Distinguish from A (Fist). 
            # In C, fingers are open but curved. In A, they are folded flat.
            # Using simple heuristic: Fist = A/S/E. 
            # Let's map Fist to A for now.
            return "A" 

        # D: Index Up, others closed (touching thumb)
        if i and not m and not r and not p:
            if tm_touch or ti_touch: # Precision
                return "D"
            return "D" # Looser
            
        # E: All Closed (Thumb tucked under fingers) - Hard to dist from A/S
        # Skipped for simplicity or mapped to A
        
        # F: Index+Thumb Touch (Circle), Others Open
        if m and r and p and ti_touch:
             return "F"
             
        # G: Index sideways... geometry hard from frontal view. 
        # Often looks like 'H' or 'D'.
        
        # H: Index+Middle sideways...
        
        # I: Pinky Up
        if p and not i and not m and not r:
            return "I"
            
        # K: Index Up, Middle Up (but thumb in between). 
        # V vs K: V = Index+Middle Up. K = Thumb intersect.
        
        # L: Thumb + Index
        if t and i and not m and not r and not p:
            return "L"
            
        # M: 3 fingers folded over thumb? 
        # Usually represented as Fist with thumb peeking between Ring/Pinky. Hard.
        
        # N: 2 fingers folded over thumb
        
        # O: All fingers touch thumb (Circle)
        if ti_touch and tm_touch and not i and not m:
             return "O"
             
        # R: Index + Middle Crossed (Twisted)
        # Hard to see crossing. Usually looks like U/V.
        
        # S: Fist with thumb FRONT (A is thumb SIDE).
        # Mapped to A for now.
        
        # T: Thumb between Index/Middle.
        
        # U: Index+Middle Up AND TOGETHER
        if i and m and not r and not p:
            if f['index_middle_touch']:
                return "U"
            else:
                return "V"
                
        # V: Index+Middle Up SEPARATE (Covered by U elses)
        
        # W: Index, Middle, Ring
        if i and m and r and not p:
            return "W"
            
        # X: Index Bent (Hook), others closed
        # Hard: Index is 'Bent' by definition so it fails 'i' check.
        
        # Y: Thumb + Pinky
        if t and p and not i and not m and not r:
            return "Y"
            
        # SP: Open Hand (5)
        if t and i and m and r and p:
            return "SPACE"
            
        return ""

    def process(self, char):
        self.history.append(char)
        # Fast response
        if not char: return None
        # Mode of buffer
        if self.history.count(char) >= 3:
            return char
        return None

# --- VISUALIZER ---
class CyberHUD:
    def __init__(self):
        self.sentence = ""
        self.last_action = 0
        # macOS native TTS is more stable than pyttsx3 in loops
        
        # Colors
        self.NEON_CYAN = (255, 255, 0)
        self.NEON_MAGENTA = (200, 0, 200)
        self.NEON_GREEN = (0, 255, 50)
        self.NEON_RED = (0, 0, 255)
        
    def say_text(self):
        if not self.sentence: return
        
        def _speak():
            # Use macOS 'say' command
            sanitized = self.sentence.replace("'", "")
            os.system(f"say '{sanitized}'")
            
        threading.Thread(target=_speak).start()
        self.sentence = "" # Clear buffer
        
    def draw_styled_landmarks(self, image, landmarks):
        h, w, _ = image.shape
        connections = HAND_CONNECTIONS
        
        for conn in connections:
            start = landmarks[conn[0]]
            end = landmarks[conn[1]]
            p1 = (int(start.x * w), int(start.y * h))
            p2 = (int(end.x * w), int(end.y * h))
            
            cv2.line(image, p1, p2, (0, 50, 50), 4) 
            cv2.line(image, p1, p2, self.NEON_CYAN, 1) 
            
        for lm in landmarks:
            px, py = int(lm.x * w), int(lm.y * h)
            cv2.circle(image, (px, py), 3, self.NEON_MAGENTA, -1)

    def draw_interface(self, image, current_char, action_text=""):
        h, w, _ = image.shape
        
        # Top Bar
        cv2.rectangle(image, (0, 0), (w, 80), (10, 10, 10), -1)
        cv2.line(image, (0, 80), (w, 80), self.NEON_CYAN, 2)
        
        # Sentence
        text = f"TEXT: {self.sentence}"
        cv2.putText(image, text, (20, 55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, self.NEON_GREEN, 2, cv2.LINE_AA)
        
        # Cursor
        if int(time.time() * 2) % 2 == 0:
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
            cv2.line(image, (20 + tw + 5, 30), (20 + tw + 5, 60), self.NEON_GREEN, 2)

        # Detected Char
        if current_char and len(current_char) == 1:
            cv2.putText(image, f"CHAR: {current_char}", (20, 150), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, self.NEON_MAGENTA, 2)

        # Action Feedback
        if action_text:
            cv2.putText(image, f"ACTION: {action_text}", (w//2 - 150, h//2), 
               cv2.FONT_HERSHEY_DUPLEX, 1.5, self.NEON_RED, 3)

    def update_logic(self, char, command):
        now = time.time()
        if now - self.last_action < 1.0: return # Cooldown ensures no double speaks/deletes
        
        if command == "SPACE":
            self.sentence += " "
            self.last_action = now
            return "SPACE"
        elif command == "BACKSPACE":
            self.sentence = self.sentence[:-1]
            self.last_action = now
            return "DELETE"
        elif command == "SPEAK":
            self.say_text()
            self.last_action = now
            return "SPEAKING"
        elif char and len(char) == 1:
            # Type char
            if not self.sentence.endswith(char) or (now - self.last_action > 1.5):
                self.sentence += char
                self.last_action = now
        return None

# --- MAIN ---
def main():
    try:
        download_model()
    except: pass

    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    # Enable 2 hands for clap detection
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=2, 
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    hud = CyberHUD()
    classifier = SignClassifier()
    
    cap = cv2.VideoCapture(0)
    # Lower res for speed if needed, but 720p is fine for M3
    cap.set(3, 1280)
    cap.set(4, 720)
    
    # Motion vars
    prev_wrist_x = 0
    
    print("STARTING_ENGINE...")
    
    with HandLandmarker.create_from_options(options) as landmarker:
        while True:
            try:
                ret, frame = cap.read()
                if not ret: break
                
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                frame_ms = int(time.time() * 1000)
                
                # Detect
                result = landmarker.detect_for_video(mp_image, frame_ms)
                
                command = None
                current_char = ""
                
                # --- VISUAL CLAP DETECTION ---
                # Checks if 2 hands are present and palms are touching
                if len(result.hand_landmarks) == 2:
                    h1 = result.hand_landmarks[0][0] # Wrist 1
                    h2 = result.hand_landmarks[1][0] # Wrist 2
                    
                    dist = math.hypot(h1.x - h2.x, h1.y - h2.y)
                    # Threshold for "Clap"
                    if dist < 0.15:
                        command = "SPEAK"
                
                # --- SINGLE HAND LOGIC ---
                if result.hand_landmarks:
                    # Just track the first hand for typing to avoid confusion
                    landmarks = result.hand_landmarks[0]
                    hud.draw_styled_landmarks(frame, landmarks)
                    
                    # 1. Classify
                    raw = classifier.classify(landmarks)
                    current_char = classifier.process(raw)
                    
                    # 2. Motion (Swipe)
                    # 'SPACE' char + moving right = Space
                    curr_x = landmarks[0].x
                    dx = curr_x - prev_wrist_x
                    
                    if abs(dx) > 0.05: # Motion detected
                        if dx > 0 and raw == "SPACE": # Moving Right with Open Hand
                            command = "SPACE"
                        elif dx < 0 and raw == "A": # Moving Left with Fist/Palm
                             # Let's make Backspace easier: Just swipe left with FIST (A) or OPEN
                             command = "BACKSPACE"

                    prev_wrist_x = curr_x
                
                # Update HUD
                feedback = hud.update_logic(current_char, command)
                
                hud.draw_interface(frame, current_char, feedback)
                
                cv2.imshow('Sign Language AI', frame)
                if cv2.waitKey(1) == 27: break
                
            except Exception as e:
                print(f"Frame Error: {e}")
                continue
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
