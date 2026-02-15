import cv2
import mediapipe as mp
import time
import webbrowser
import os
import math

# -------------------------------------------------------------------------
# SETUP & CONFIGURATION
# -------------------------------------------------------------------------
# Installation Requirements:
# pip install -r requirements.txt
# OR
# pip install opencv-python mediapipe

COOLDOWN_SECONDS = 5.0
HUD_COLOR = (255, 255, 0)  # Cyan (BGR format for OpenCV is (255, 255, 0))
TEXT_COLOR = (0, 255, 0)   # Green for Ready
WARN_COLOR = (0, 0, 255)   # Red for Cooldown

# Gesture URLs
URLS = {
    "JAZZ": "https://www.youtube.com/results?search_query=smooth+jazz",
    "ROCK": "https://www.youtube.com/results?search_query=heavy+metal+rock",
    "HIPHOP": "https://www.youtube.com/results?search_query=90s+hip+hop",
    "HIGH_FIVE": "https://www.youtube.com/", # Main page as stop/pause proxy
    "THUMBS_UP": "https://www.youtube.com/playlist?list=LL" # Liked videos
}

# -------------------------------------------------------------------------
# HAND DETECTOR CLASS (UPDATED FOR MEDIAPIPE TASKS API)
# -------------------------------------------------------------------------
class HandDetector:
    def __init__(self, model_path='hand_landmarker.task', max_hands=1, detection_con=0.7, track_con=0.5):
        self.model_path = model_path
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        self.results = None
        self.tip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips

        # Check if model exists
        if not os.path.exists(self.model_path):
            print(f"Error: Model file {self.model_path} not found.")
            print("Downloading model file automatically...")
            os.system(f"curl -o {self.model_path} https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
            if not os.path.exists(self.model_path):
                 raise FileNotFoundError(f"Failed to download model file {self.model_path}.")

        # Import Tasks API
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        # Create HandLandmarker
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_con,
            min_hand_presence_confidence=self.track_con,
            min_tracking_confidence=self.track_con
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def find_hands(self, img, timestamp_ms, draw=True):
        # MediaPipe Tasks requires mp.Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Perform detection
        try:
             self.results = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
             # print(f"Detection failed: {e}") # Debug only
             self.results = None

        if self.results and self.results.hand_landmarks:
             for hand_landmarks in self.results.hand_landmarks:
                if draw:
                    self.draw_landmarks_custom(img, hand_landmarks)
        
        return img

    def draw_landmarks_custom(self, img, landmarks):
        # Custom drawing function
        h, w, c = img.shape
        points = []
        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            points.append((cx, cy))
            cv2.circle(img, (cx, cy), 5, (0, 255, 255), cv2.FILLED) # Landmarks Cyan/Yellow
        
        # Define connections (Standard Hand)
        connections = [
            (0,1), (1,2), (2,3), (3,4),       # Thumb
            (0,5), (5,6), (6,7), (7,8),       # Index
            (5,9), (9,10), (10,11), (11,12),  # Middle
            (9,13), (13,14), (14,15), (15,16),# Ring
            (13,17), (17,18), (18,19), (19,20),# Pinky
            (0,17), (5,9), (9,13), (13,17)    # Palm
        ]
        
        for p1, p2 in connections:
             if p1 < len(points) and p2 < len(points):
                cv2.line(img, points[p1], points[p2], (255, 255, 0), 2) # Connections Cyan

    def find_position(self, img, hand_no=0):
        lm_list = []
        if self.results and self.results.hand_landmarks:
            if hand_no < len(self.results.hand_landmarks):
                my_hand = self.results.hand_landmarks[hand_no]
                h, w, c = img.shape
                for id, lm in enumerate(my_hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
        return lm_list

    def fingers_up(self, lm_list):
        fingers = []
        if not lm_list:
             return [0,0,0,0,0]
        
        # Thumb Heuristic: Distance check
        # dist(0,4) > dist(0,3) + margin implies extended
        def dist(i1, i2):
             return math.hypot(lm_list[i1][1]-lm_list[i2][1], lm_list[i1][2]-lm_list[i2][2])
             
        if dist(0, 4) > dist(0, 3) + 20: 
             fingers.append(1)
        else:
             fingers.append(0)

        # Fingers 1-4
        for id in range(1, 5):
            if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------
def main():
    cap = cv2.VideoCapture(0)
    # Camera fix attempt for MacOS
    cap.set(3, 1280)
    cap.set(4, 720)
    
    if not cap.isOpened():
        print("Error: Camera not accessible. Try checking permissions.")
        # Sometimes index 1 works if 0 fails
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
             print("Error: Camera 1 also not accessible.")
             return

    try:
        detector = HandDetector()
    except Exception as e:
        print(f"Failed to initialize detector: {e}")
        return
    
    last_action_time = 0.0
    p_time = 0
    start_time_ms = int(time.time() * 1000)
    
    print("AI Gesture DJ Controller Started...")
    print("Press 'q' to quit.")

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to read frame.")
            break
        
        # Flip image for mirror effect
        img = cv2.flip(img, 1) # 1 for horizontal flip
        
        # Calculate timestamp for MediaPipe
        current_time_ms = int(time.time() * 1000)
        timestamp = current_time_ms - start_time_ms

        # Detect Hands
        try:
             img = detector.find_hands(img, timestamp)
             lm_list = detector.find_position(img)
        except Exception as e:
             print(f"Detection error: {e}")
             lm_list = []
        
        current_time_sec = time.time()
        cooldown_remaining = max(0.0, COOLDOWN_SECONDS - (current_time_sec - last_action_time))
        is_cooldown = cooldown_remaining > 0
        
        detected_gesture = "NONE"
        target_action = None
        
        if len(lm_list) != 0:
            fingers = detector.fingers_up(lm_list)
            
            # Gesture Logic
            # 1. The Jazz Finger (Index Only)
            if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                 detected_gesture = "JAZZ FINGER"
                 target_action = "JAZZ"

            # 2. Rock on / Metal (Index & Pinky Up, Thumb Down)
            elif fingers[1] == 1 and fingers[4] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[0] == 0:
                 detected_gesture = "ROCK ON"
                 target_action = "ROCK"

            # 3. Victory / HipHop (Index & Middle Up)
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                 detected_gesture = "PEACE / HIPHOP"
                 target_action = "HIPHOP"

            # 4. High Five / Stop (All Open)
            elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                 detected_gesture = "HIGH FIVE"
                 target_action = "HIGH_FIVE"
            
            # 5. Thumbs Up (Thumb Only)
            elif fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                 detected_gesture = "THUMBS UP"
                 target_action = "THUMBS_UP"
            
            if target_action:
                if not is_cooldown:
                    print(f"Executing Action: {target_action}")
                    webbrowser.open(URLS[target_action])
                    last_action_time = time.time()
                    is_cooldown = True 
        
        # ---------------------------------------------------------------------
        # HUD DRAWING
        # ---------------------------------------------------------------------
        c_time = time.time()
        fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
        p_time = c_time
        
        cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
        
        if is_cooldown:
            status_text = f"SYSTEM: COOLDOWN ({cooldown_remaining:.1f}s)"
            cv2.putText(img, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, WARN_COLOR, 2)
        else:
            status_text = "SYSTEM: READY"
            cv2.putText(img, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, TEXT_COLOR, 2)

        if detected_gesture != "NONE":
             cv2.putText(img, f"GESTURE: {detected_gesture}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, HUD_COLOR, 2)
        
        cv2.imshow("AI Gesture DJ Controller", img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
