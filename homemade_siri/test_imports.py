try:
    import speech_recognition as sr
    print("speech_recognition imported successfully")
    import pyttsx3
    print("pyttsx3 imported successfully")
    import google.generativeai as genai
    print("google.generativeai imported successfully")
    import psutil
    print("psutil imported successfully")
    import pyautogui
    print("pyautogui imported successfully")
    import pyaudio
    print("pyaudio imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    exit(1)
