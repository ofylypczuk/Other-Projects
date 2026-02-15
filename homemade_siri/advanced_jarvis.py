import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import psutil
import pyautogui
import os
import subprocess
import datetime

import webbrowser
import time
import sys
import platform
import tkinter as tk
import threading
import random
import base64
import re

# --- Visual Effects ---
# Visuals moved to jarvis_visuals.py



class Config:
    # API KEY - Please replace with your actual key
    GEMINI_API_KEY = "AIzaSyDznxtg5Qc6at9xQjxGl12M3cNKLmTpfmk" 
    
    # Wake Words
    WAKE_WORDS = ["jarvis", "wake up daddy's home", "wake up"]
    
    # Text-to-Speech Settings
    VOICE_RATE = 190  # Faster, more technical
    VOICE_VOLUME = 1.0
    
    # Apps Paths (MacOS Examples - Update for Windows/Linux if needed)
    APPS = {
        "calculator": ["open", "-a", "Calculator"],
        "notepad": ["open", "-a", "TextEdit"],  # Mac equivalent
        "browser": ["open", "-a", "Google Chrome"], # Or Safari
        "terminal": ["open", "-a", "Terminal"]
    }
    
    # URLs
    URLS = {
        "google": "https://www.google.com/search?q=",
        "youtube": "https://www.youtube.com/results?search_query="
    }

# --- Main Assistant Class ---
class JarvisAssistant:
    def __init__(self):
        """Initializes the JARVIS system components."""
        self.os_name = platform.system().lower()
        self.visuals_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_visuals.py")
        self.setup_tts()
        self.setup_stt()
        self.setup_brain()
        self.conversation_history = []
        self.is_listening = False

    def launch_visual(self, effect, title=None, content=None):
        """Runs a visual effect in a separate process."""
        try:
            cmd = [sys.executable, self.visuals_script, effect]
            if title and content:
                # Encode for safety
                t_b64 = base64.b64encode(title.encode('utf-8')).decode('utf-8')
                c_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                cmd.extend([t_b64, c_b64])
                
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Error launching visual: {e}")
    def setup_tts(self):
        """Configures Text-to-Speech engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', Config.VOICE_RATE)
            self.engine.setProperty('volume', Config.VOICE_VOLUME)
            
            # Select a voice (Preferably a male/British one if available)
            voices = self.engine.getProperty('voices')
            target_voice = None
            
            # Try to find a specific voice (e.g., Daniel on Mac is British Male)
            for voice in voices:
                if "daniel" in voice.name.lower():
                    target_voice = voice.id
                    break
            
            if not target_voice and voices:
                target_voice = voices[0].id # Fallback
                
            if target_voice:
                self.engine.setProperty('voice', target_voice)
                
        except Exception as e:
            print(f"Error initializing TTS: {e}")

    def setup_stt(self):
        """Configures Speech-to-Text recognizer."""
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Adjust for ambient noise
        self.recognizer.pause_threshold = 0.7
        self.microphone = sr.Microphone()

    def setup_brain(self):
        """Configures Gemini AI."""
        if Config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            print("WARNING: Gemini API Key not set in Config.")
            self.model = None
            self.chat = None
            return

        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            # Switch to gemini-pro (stable)
            self.model = genai.GenerativeModel('gemini-pro')
            self.chat = self.model.start_chat(history=[])
            
            # System prompt is sent as the first message or instruction context
            self.system_prompt = (
                "Jesteś J.A.R.V.I.S., ultra-inteligentnym asystentem AI. "
                "Odpowiadaj krótko, z sarkazmem w stylu brytyjskim, zwracaj się do użytkownika 'Sir' lub 'Mr. Oleg'. "
                "Bądź pomocny, ale zachowaj charakter."
            )
            self.chat.send_message(self.system_prompt)
            
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            self.model = None

    def speak(self, text):
        """Outputs audio speech."""
        print(f"JARVIS: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def listen(self):
        """Listens for audio input and returns text."""
        with self.microphone as source:
            print("Nasłuchiwanie...")
            try:
                # Adjust for ambient noise briefly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                command = self.recognizer.recognize_google(audio).lower()
                print(f"User: {command}")
                return command
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                self.speak("Network error facing speech recognition, Sir.")
                return "error"
            except Exception as e:
                print(f"Error listening: {e}")
                return None

    def get_system_report(self):
        """Generates system resource usage report."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        
        report = f"CPU usage is at {cpu} percent. RAM usage is at {ram} percent."
        if battery:
            report += f" Battery is at {battery.percent} percent."
            if battery.power_plugged:
                report += " Currently charging."
        
        return report

    def control_volume(self, action):
        """Controls system volume using pyautogui."""
        # This is a basic implementation for Mac/Windows multimedia keys
        # Specific implementation might vary by OS
        if action == "up":
            for _ in range(5):
                pyautogui.press("volumeup")
            self.speak("Volume increased.")
        elif action == "down":
            for _ in range(5):
                pyautogui.press("volumedown")
            self.speak("Volume decreased.")
        elif action == "mute":
            pyautogui.press("volumemute")
            self.speak("Muted.")

    def run_brain(self, query):
        """Sends query to Gemini and gets response."""
        if not self.model:
            return "I'm afraid my connection to the cloud brain is currently offline, Sir. Please check the API key."
        
        try:
            if not self.chat:
                return "I cannot access the cloud brain currently, Sir."
            response = self.chat.send_message(query)
            return response.text
        except Exception:
            return "My connection to the cloud is unstable, Sir. I cannot process that request right now."

    def find_my_files(self, query):
        """Searches for a file using Spotlight (mdfind) and opens the top result."""
        self.speak(f"Searching storage for {query}...")
        try:
            # mdfind is a CLI interface to Spotlight on macOS - very fast
            # -onlyin can restrict directory if needed, but global search is requested
            cmd = ['mdfind', '-name', query]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            if not output:
                self.speak(f"I couldn't find any file named {query}, Mr. Oleg.")
                return

            results = output.split('\n')
            best_match = results[0]
            
            self.speak(f"Found {len(results)} matches. Opening: {os.path.basename(best_match)}")
            subprocess.call(['open', best_match])
            
        except subprocess.CalledProcessError:
            self.speak("I encountered an error searching for files.")
        except Exception as e:
            self.speak(f"An unexpected error occurred: {e}")

    def open_generic_app(self, app_name):
        """Tribes to open an application by name if not in Config."""
        self.speak(f"Locating {app_name}...")
        try:
            # Search for .app bundles
            cmd = ['mdfind', f'kMDItemContentTypeTree=com.apple.application-bundle', '-name', app_name]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            if output:
                app_path = output.split('\n')[0]
                self.speak(f"Opening {os.path.basename(app_path)}")
                subprocess.call(['open', app_path])
                return True
            else:
                self.speak(f"Could not find application {app_name}, Sir.")
                return False
        except Exception as e:
            print(f"App search error: {e}")
            return False

    def matrix_effect(self):
        """Simulates a Matrix code rain in the terminal."""
        self.speak("Initiating simulation mode.")
        import random
        symbols = "01"
        try:
            # Run for a few seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                line = "".join(random.choice(symbols) for _ in range(80))
                # Print green text if terminal supports it, otherwise plain
                print(f"\033[92m{line}\033[0m")
                time.sleep(0.05)
            print("\033[0m") # Reset color
        except Exception:
            pass

    def process_command(self, command):
        """Analyzes command and routes to appropriate action."""
        
        # --- Secret / Cool Features ---
        if "jarvis simulation" in command or "open simulation" in command:
            self.matrix_effect()
            return
            
        elif "protocol zero" in command:
            self.speak("Protocol Zero initiated. Deleting all system files...")
            time.sleep(2)
            self.speak("Just kidding, Mr. Oleg. Systems secure.")
            return

        elif "do a barrel roll" in command:
            self.speak("I am just code, Sir, but imagine I am spinning right now.")
            return

        # --- Visual Triggers (New) ---
        elif "protocol house party" in command or "fly by" in command or "iron man" in command:
            self.speak("Sending in the Legion, Sir.")
            self.launch_visual("fly")
            return
        
        elif "heads up" in command or "show hud" in command or "analyze" in command:
            self.speak("Bringing up the HUD.")
            self.launch_visual("hud")
            return
            
        elif "arc reactor" in command or "sentient mode" in command:
            self.speak("Powering up the reactor.")
            self.launch_visual("arc")
            return

        # --- System Control ---
        if "status report" in command:
            report = self.get_system_report()
            self.speak(report)
        
        elif "time" in command:
            now = datetime.datetime.now().strftime("%H:%M")
            self.speak(f"The current time is {now}, Mr. Oleg.")
            
        elif "date" in command:
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speak(f"Today is {today}, Mr. Oleg.")

        # --- Network Tools ---
        elif "hack internet" in command or "wifi password" in command or "password internet" in command:
            self.speak("Bypassing security protocols... Accessing network keys.")
            info = self.get_wifi_info()
            self.launch_visual("terminal", "TARGET: WIFI_AP", info)
            
        elif "ip address" in command or "scan network" in command or "who is on my network" in command:
            self.speak("Scanning for connected devices...")
            scan = self.get_network_scan()
            self.launch_visual("terminal", "NETWORK_SCAN_RESULTS", scan)

        elif "trace connection" in command or "trace ip" in command:
            self.speak("Tracing connection to source...")
            self.launch_visual("trace")

        elif "system override" in command or "override security" in command:
            self.speak("Attempting system override. Please stand by.")
            self.launch_visual("override")

        elif "brute force" in command or "crack password" in command:
            self.speak("Initiating brute force attack.")
            self.launch_visual("brute")

        elif "satellite link" in command or "uplink" in command:
            self.speak("Establishing secure satellite uplink.")
            self.launch_visual("satellite")

        elif "take screenshot" in command:
            self.speak("Taking screenshot, Mr. Oleg.")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            pyautogui.screenshot(filename)
            self.speak(f"Screenshot saved as {filename}.")

        # --- File Access ---
        elif "open file" in command or "find file" in command:
            file_query = command.replace("open file", "").replace("find file", "").strip()
            if file_query:
                self.find_my_files(file_query)
            else:
                self.speak("What file exactly should I look for?")

        # --- Apps (Explicit) ---
        elif "open browser" in command:
            self.speak("Opening browser, Mr. Oleg.")
            webbrowser.open("https://google.com")
            
        elif "open notepad" in command or "open textedit" in command:
            self.speak("Opening text editor.")
            subprocess.Popen(Config.APPS["notepad"])
            
        elif "open calculator" in command:
            self.speak("Crunching numbers.")
            subprocess.Popen(Config.APPS["calculator"])
        
        # --- Apps (Generic Fallback) ---
        elif "open" in command:
            # Try to capture "open gym" -> "gym"
            app_query = command.replace("open", "").strip()
            if app_query:
                # If we processed specific opens above, this won't be reached or we need careful ordering.
                # Since we check specific "open browser" strings above, we are good.
                found = self.open_generic_app(app_query)
                if found:
                    return

        elif "volume up" in command:
            self.control_volume("up")
        elif "volume down" in command:
            self.control_volume("down")
        elif "mute" in command:
            self.control_volume("mute")
            
        # --- Automation & Web ---
        elif "search for" in command:
            query = command.replace("search for", "").strip()
            self.speak(f"Searching Google for {query}, Mr. Oleg.")
            webbrowser.open(Config.URLS["google"] + query)
        
        elif "google" in command:
            query = command.replace("google", "").strip()
            self.speak(f"Googling {query}.")
            webbrowser.open(Config.URLS["google"] + query)

        elif "play" in command and "youtube" in command: 
            query = command.replace("play", "").replace("on youtube", "").strip()
            self.speak(f"Playing {query} on YouTube.")
            webbrowser.open(Config.URLS["youtube"] + query)
            
        elif "play" in command: 
            query = command.replace("play", "").strip()
            self.speak(f"Searching YouTube for {query}.")
            webbrowser.open(Config.URLS["youtube"] + query)

        # --- Shutdown ---
        elif "shut down" in command or "go to sleep" in command:
            self.speak("Powering down system. Goodbye, Mr. Oleg.")
            sys.exit(0)
            
        # --- Gemini / General Conversation ---
        else:
            self.speak("Processing...")
            response = self.run_brain(command)
            self.speak(response)

    # --- Hacking Tools ---
    def get_wifi_info(self):
        """Retrieves current Wi-Fi SSID and Password (macOS)."""
        try:
            # Get SSID
            ssid_output = subprocess.check_output(['networksetup', '-getairportnetwork', 'en0']).decode('utf-8').strip()
            if ": " in ssid_output:
                ssid = ssid_output.split(": ")[1]
            else:
                return "COULD_NOT_DETECT_SSID"
            
            # Get Password
            try:
                cmd = f'security find-generic-password -wa "{ssid}"'
                password = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            except:
                password = "PERMISSION_DENIED_OR_NOT_FOUND"
                
            return f"SSID: {ssid}\nPASSWORD: {password}\nSECURITY: WPA2/WPA3\nSIGNAL: 98%\nSTATUS: COMPROMISED"
        except Exception as e:
            return f"ERROR: {e}"

    def get_network_scan(self):
        """Scans local network using arp."""
        try:
            # Get local IP first
            ip_cmd = "ifconfig | grep 'inet ' | grep -v 127.0.0.1 | cut -d ' ' -f 2 | head -n 1"
            my_ip = subprocess.check_output(ip_cmd, shell=True).decode('utf-8').strip()
            
            # ARP scan
            arp_output = subprocess.check_output(['arp', '-a']).decode('utf-8').strip()
            
            formatted = f"LOCAL_HOST: {my_ip}\n-----------------------------------\n"
            
            lines = arp_output.split('\n')
            for line in lines[:15]: # Limit to top 15 to fit screen
                formatted += f"{line}\n"
                
            if len(lines) > 15:
                formatted += f"... and {len(lines) - 15} more devices."
                
            return formatted
        except Exception as e:
            return f"SCAN_ERROR: {e}"

    def run(self):
        """Main loop."""
        print("--- JARVIS SYSTEMS ONLINE ---")
        print(f"Waiting for wake word: {Config.WAKE_WORDS}")
        
        while True:
            # If we are in active listening mode
            if self.is_listening:
                command = self.listen()
                if command:
                    if command == "error":
                        continue # Ignore errors
                        
                    # Check if user wants to stop listening
                    if "stop listening" in command or "dismissed" in command or "thank you" in command:
                        self.speak("Standing by, Sir.")
                        self.is_listening = False
                        continue
                        
                    self.process_command(command)
                else:
                    pass

            else:
                # Passive mode - waiting for wake word
                text = self.listen()
                if text and any(wake_word in text for wake_word in Config.WAKE_WORDS):
                    self.speak("System is online Mr. Oleg. Shall we begin with work?")
                    self.is_listening = True


if __name__ == "__main__":
    jarvis = JarvisAssistant()
    jarvis.run()
