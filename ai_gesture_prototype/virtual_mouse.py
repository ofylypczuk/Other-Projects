import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
import os
import sys
from collections import deque

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
CAM_WIDTH, CAM_HEIGHT = 640, 480
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
FRAME_REDUCTION = 100 

# Colors
COLOR_CYAN = (255, 255, 0)
COLOR_MAGENTA = (255, 0, 255)
COLOR_GOLD = (0, 215, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_HUD_BG = (15, 15, 15)

# Smoothing (Adaptive)
MIN_SMOOTHING = 2
MAX_SMOOTHING = 5
prev_x, prev_y = 0, 0
curr_x, curr_y = 0, 0

# App Config
last_app_trigger_time = 0
APP_COOLDOWN = 1.5

# Scroll State
scroll_mode = "IDLE" 
SCROLL_SPEED = 15

# Blink Config
blink_active = False 
blink_start_time = 0
last_blink_time = 0
BLINK_COOLDOWN = 0.5

# Gesture Config
OPEN_COOLDOWN = 1.0
last_open_time = 0

# Tasks API Setup
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

HAND_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
FACE_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')

# ---------------------------------------------------------
# UTILS
# ---------------------------------------------------------
def draw_hud(img, fps, mode, scroll_status, blink_visual):
    h, w, c = img.shape
    overlay = img.copy()
    
    # Status Panel
    cv2.rectangle(overlay, (20, 20), (350, 160), COLOR_HUD_BG, -1)
    cv2.rectangle(overlay, (20, 20), (350, 160), COLOR_CYAN, 1)
    
    cv2.putText(overlay, f"FPS: {int(fps)}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_GREEN, 1)
    cv2.putText(overlay, f"MODE: {mode}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_GOLD, 1)
    
    status_color = COLOR_RED if scroll_status != "IDLE" else COLOR_WHITE
    cv2.putText(overlay, f"SCROLL: {scroll_status}", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1)

    if blink_visual:
         cv2.putText(overlay, f"ACTION: {blink_visual}", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_MAGENTA, 2)

    # Valid Area
    cv2.rectangle(overlay, (FRAME_REDUCTION, FRAME_REDUCTION), 
                  (w - FRAME_REDUCTION, h - FRAME_REDUCTION), (50, 50, 50), 1)

    # Edge Swipe Zones
    cv2.line(overlay, (50, 0), (50, h), COLOR_RED, 1)
    cv2.line(overlay, (w-50, 0), (w-50, h), COLOR_RED, 1)
    
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    return img

def main():
    global prev_x, prev_y, curr_x, curr_y, last_app_trigger_time, scroll_mode
    global blink_active, blink_start_time, last_blink_time, last_open_time

    if not os.path.exists(HAND_MODEL_PATH) or not os.path.exists(FACE_MODEL_PATH):
        print(f"Models not found.\nHand: {HAND_MODEL_PATH}\nFace: {FACE_MODEL_PATH}")
        return

    cap = cv2.VideoCapture(0)
    cap.set(3, CAM_WIDTH)
    cap.set(4, CAM_HEIGHT)

    # Hand Options
    hand_options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5)

    # Face Options
    face_options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=FACE_MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_face_blendshapes=True)

    print("JARVIS V8 (Peace to Open) Initialized. 'q' to exit.")
    
    with HandLandmarker.create_from_options(hand_options) as hand_landmarker, \
         FaceLandmarker.create_from_options(face_options) as face_landmarker:
        
        while True:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int(time.time() * 1000)
            
            # Detect
            hand_result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)
            face_result = face_landmarker.detect_for_video(mp_image, timestamp_ms)
            
            mode_text = "STANDBY"
            current_time = time.time()
            action_visual = ""
            
            # -------------------------------------------------
            # 1. BLINK LOGIC (SINGLE CLICK / SELECT)
            # -------------------------------------------------
            if face_result.face_blendshapes:
                shapes = face_result.face_blendshapes[0]
                blink_left = 0
                blink_right = 0
                for category in shapes:
                    if category.category_name == 'eyeBlinkLeft': blink_left = category.score
                    elif category.category_name == 'eyeBlinkRight': blink_right = category.score
                
                eyes_closed = (blink_left > 0.5 and blink_right > 0.5)
                
                if eyes_closed and not blink_active:
                    blink_active = True
                    blink_start_time = current_time
                elif not eyes_closed and blink_active:
                    blink_active = False
                    duration = current_time - blink_start_time
                    if 0.05 < duration < 0.8: 
                        if current_time - last_blink_time > BLINK_COOLDOWN:
                            pyautogui.click()
                            print("ACTION: BLINK -> CLICK (SELECT)")
                            action_visual = "BLINK: SELECT"
                            last_blink_time = current_time
            
            # -------------------------------------------------
            # 2. HAND LOGIC
            # -------------------------------------------------
            if hand_result.hand_landmarks:
                hand_lms = hand_result.hand_landmarks[0]
                h, w, _ = frame.shape
                
                def to_px(lm): return int(lm.x * w), int(lm.y * h)
                wrist = to_px(hand_lms[0])
                index_tip = to_px(hand_lms[8])
                middle_tip = to_px(hand_lms[12])
                ring_tip = to_px(hand_lms[16])
                thumb_tip = to_px(hand_lms[4])
                
                # Draw
                connections = [
                    (0,1), (1,2), (2,3), (3,4), (0,5), (5,6), (6,7), (7,8),
                    (9,10), (10,11), (11,12), (13,14), (14,15), (15,16),
                    (0,17), (17,18), (18,19), (19,20), (5,9), (9,13), (13,17)
                ]
                px_points = [to_px(lm) for lm in hand_lms]
                for s, e in connections:
                    cv2.line(frame, px_points[s], px_points[e], COLOR_CYAN, 1)
                
                # Fingers Up Logic
                index_up = hand_lms[8].y < hand_lms[6].y
                middle_up = hand_lms[12].y < hand_lms[10].y
                ring_up = hand_lms[16].y < hand_lms[14].y
                pinky_up = hand_lms[20].y < hand_lms[18].y
                thumb_up = hand_lms[4].x < hand_lms[3].x 
                
                count_fingers = sum([index_up, middle_up, ring_up, pinky_up])
                if thumb_up: count_fingers += 1

                # -------------------------------------------------
                # GESTURES
                # -------------------------------------------------

                # A. EDGE SWIPE (Minimize)
                if wrist[0] < 50 or wrist[0] > w - 50:
                    if current_time - last_app_trigger_time > APP_COOLDOWN:
                        print("EDGE DETECTED -> MINIMIZE")
                        pyautogui.hotkey('command', 'f3') # Show Desktop
                        last_app_trigger_time = current_time
                        mode_text = "MINIMIZING"

                # B. SCROLL JOYSTICK (Three Fingers: Index, Middle, Ring)
                elif index_up and middle_up and ring_up and not pinky_up:
                    mode_text = "SCROLL (3 FINGERS)"
                    y_pos = hand_lms[0].y 
                    
                    if y_pos < 0.3:
                        scroll_mode = "UP"
                        pyautogui.scroll(SCROLL_SPEED)
                        cv2.putText(frame, "^^ UP ^^", (w//2, h//2-50), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_GOLD, 2)
                    elif y_pos > 0.7:
                        scroll_mode = "DOWN"
                        pyautogui.scroll(-SCROLL_SPEED)
                        cv2.putText(frame, "vv DOWN vv", (w//2, h//2+50), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_GOLD, 2)
                    else:
                        scroll_mode = "IDLE (HOLD)"

                # C. LAUNCHPAD (Open Hand - 4/5 Fingers)
                elif count_fingers >= 4:
                    mode_text = "OPEN HAND"
                    scroll_mode = "IDLE"
                    if 0.2 < hand_lms[0].x < 0.8:
                        if current_time - last_app_trigger_time > APP_COOLDOWN:
                            os.system("open -a Launchpad")
                            last_app_trigger_time = current_time

                # D. OPEN FILE (Two Fingers "Peace" - Index + Middle)
                elif index_up and middle_up and not ring_up and not pinky_up:
                    mode_text = "PEACE: OPEN FILE"
                    scroll_mode = "IDLE"
                    
                    if current_time - last_open_time > OPEN_COOLDOWN:
                        pyautogui.doubleClick()
                        print("ACTION: 2 FINGERS -> OPEN")
                        # Visual Feedback burst
                        cv2.circle(frame, index_tip, 20, COLOR_GREEN, 3)
                        cv2.circle(frame, middle_tip, 20, COLOR_GREEN, 3)
                        action_visual = "OPENING..."
                        last_open_time = current_time

                # E. CURSOR (Index Only)
                elif index_up and not middle_up:
                    mode_text = "CURSOR / BLINK SELECT"
                    scroll_mode = "IDLE"
                    
                    # Mapping & Smoothing
                    x_raw = np.interp(index_tip[0], (FRAME_REDUCTION, CAM_WIDTH - FRAME_REDUCTION), (0, SCREEN_WIDTH))
                    y_raw = np.interp(index_tip[1], (FRAME_REDUCTION, CAM_HEIGHT - FRAME_REDUCTION), (0, SCREEN_HEIGHT))
                    
                    dist = math.hypot(x_raw - curr_x, y_raw - curr_y)
                    smooth_val = np.interp(dist, (0, 300), (MAX_SMOOTHING, MIN_SMOOTHING))
                    
                    curr_x = prev_x + (x_raw - prev_x) / smooth_val
                    curr_y = prev_y + (y_raw - prev_y) / smooth_val
                    
                    try:
                        pyautogui.moveTo(curr_x, curr_y)
                    except: pass
                    prev_x, prev_y = curr_x, curr_y
                    
                    cv2.circle(frame, index_tip, 8, COLOR_CYAN, -1)
                    
                    # Backup pinch
                    dist_click = math.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])
                    if dist_click < 40:
                        cv2.circle(frame, index_tip, 12, COLOR_GOLD, 2)
                        if current_time - last_app_trigger_time > 0.3: 
                             pyautogui.click() 
                             time.sleep(0.1)

            # Draw HUD
            frame = draw_hud(frame, 30, mode_text, scroll_mode, action_visual)
            cv2.imshow("JARVIS V8", frame)
            
            if cv2.waitKey(1) == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
