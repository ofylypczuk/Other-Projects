try:
    import mediapipe.python.solutions as solutions
    print("Imported mediapipe.python.solutions successfully")
    print(f"Solutions: {solutions}")
except ImportError as e:
    print(f"Failed to import mediapipe.python.solutions: {e}")

try:
    from mediapipe import solutions
    print("Imported from mediapipe import solutions successfully")
except ImportError as e:
    print(f"Failed from mediapipe import solutions: {e}")
§   