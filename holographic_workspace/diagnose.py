import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Directory contents:")
print(os.listdir("."))

try:
    import mediapipe
    print(f"MediaPipe Logged Path: {mediapipe.__file__}")
    print(f"MediaPipe Dir: {dir(mediapipe)}")
    
    import mediapipe.python.solutions as solutions
    print("Direct import of solutions successful")
except Exception as e:
    print(f"Error: {e}")

try:
    import mediapipe as mp
    print(f"mp.solutions detection: {hasattr(mp, 'solutions')}")
except:
    pass
