import mediapipe as mp
print(f"MediaPipe file: {mp.__file__}")
print(f"Dir(mp): {dir(mp)}")
try:
    print(f"Solutions: {mp.solutions}")
except AttributeError as e:
    print(f"Error accessing solutions: {e}")
