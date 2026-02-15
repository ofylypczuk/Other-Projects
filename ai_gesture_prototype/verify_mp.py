import mediapipe as mp
import sys
import os

print(f"MediaPipe version: {mp.__version__}")
try:
    print(f"File: {mp.__file__}")
except:
    print("File: Not found")

print(f"Dir: {dir(mp)}")
print(f"Path: {sys.path}")
print(f"CWD: {os.getcwd()}")

try:
    import mediapipe.python.solutions.hands as mp_hands
    print("Direct import of mediapipe.python.solutions.hands SUCCESS")
except Exception as e:
    print(f"Direct import FAILED: {e}")
