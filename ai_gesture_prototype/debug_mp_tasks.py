import mediapipe as mp
try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    print("Imported mediapipe.tasks.python.vision successfully")
    print(f"Vision dir: {dir(vision)}")
    if hasattr(vision, 'HandLandmarker'):
        print("HandLandmarker found")
    else:
        print("HandLandmarker NOT found")
except ImportError as e:
    print(f"Error importing tasks: {e}")
