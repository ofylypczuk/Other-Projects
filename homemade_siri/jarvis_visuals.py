import tkinter as tk
import sys
import random
import time

class JarvisVisuals:
    def canvas_hud(self):
        """Creates a Matrix/HUD style overlay."""
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.attributes('-alpha', 0.8) # Slight transparency
            root.configure(background='black')
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            
            canvas = tk.Canvas(root, bg='black', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            
            # Start loop
            steps = 0
            
            def draw_tech():
                nonlocal steps
                if steps > 50: # Run for ~2.5 seconds (50 * 50ms)
                    root.destroy()
                    return

                for _ in range(10): # Draw 10 items per tick
                    x = random.randint(0, width)
                    y = random.randint(0, height)
                    text_color = random.choice(['#00FF00', '#00FFFF', '#FFFFFF']) 
                    font_size = random.randint(10, 24)
                    text = random.choice(["ANALYZING", "SYSTEM OK", "UPLOADING", "010101", "TARGET LOCKED", "SECURE", "JARVIS CORE"])
                    canvas.create_text(x, y, text=text, fill=text_color, font=('Courier', font_size))
                
                steps += 1
                root.after(50, draw_tech)
                
            draw_tech()
            root.mainloop()
        except Exception:
            pass

    def arc_reactor_pulse(self):
        """Simulates an Arc Reactor pulsing in the center."""
        try:
            root = tk.Tk()
            w, h = 300, 300
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root.geometry('%dx%d+%d+%d' % (w, h, x, y))
            root.overrideredirect(True)
            root.configure(background='black')
            root.attributes('-alpha', 0.8)
            root.attributes('-topmost', True)

            canvas = tk.Canvas(root, width=w, height=h, bg='black', highlightthickness=0)
            canvas.pack()
            
            center_x, center_y = w/2, h/2
            
            step = 0
            def pulse():
                nonlocal step
                canvas.delete("all")
                
                # Pulse Logic
                import math
                glow = 10 * math.sin(step * 0.2) + 100
                
                # Blue Glow
                canvas.create_oval(center_x-glow, center_y-glow, center_x+glow, center_y+glow, fill='#00FFFF', outline='')
                # White Core
                canvas.create_oval(center_x-40, center_y-40, center_x+40, center_y+40, fill='white', outline='cyan', width=3)
                
                step += 1
                if step < 100:
                    root.after(30, pulse)
                else:
                    root.destroy()

            pulse()
            root.mainloop()
        except:
            pass

    def iron_man_fly(self):
        """Simulates Iron man flying across screen."""
        try:
            root = tk.Tk()
            w, h = 120, 60
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.configure(background='black')
            root.attributes('-alpha', 0.8) 
            
            # Start position
            y_pos = random.randint(100, hs-200)
            
            canvas = tk.Canvas(root, width=w, height=h, bg='black', highlightthickness=0)
            canvas.pack()
            
            # Draw "Iron Man" (Abstract UI representation)
            # Gold Rectangle with Red Border
            canvas.create_rectangle(5, 5, w-5, h-5, fill='#800000', outline='#FFD700', width=4)
            canvas.create_text(w/2, h/2, text="MK-85", fill='#00FFFF', font=('Arial', 10, 'bold'))
            
            width_screen = ws
            
            def fly(x=0):
                if x < width_screen:
                    root.geometry(f'{w}x{h}+{x}+{y_pos}')
                    root.after(5, lambda: fly(x+25)) # Fast speed
                else:
                    root.destroy()
            
            fly(-100)
            root.mainloop()
        except:
            pass

    def hacker_terminal(self, title_b64, content_b64):
        """Displays a hacker-style terminal with scrolling text."""
        try:
            import base64
            title = base64.b64decode(title_b64).decode('utf-8')
            content = base64.b64decode(content_b64).decode('utf-8')
        except:
            title = "SYSTEM ERROR"
            content = "COULD NOT DECODE DATA"

        top = tk.Tk()
        top.geometry("600x400")
        top.configure(background='black')
        top.attributes('-topmost', True)
        top.title(title)
        
        # Terminal look
        text_area = tk.Text(top, bg='black', fg='#00FF00', font=('Courier', 12), borderwidth=0, highlightthickness=0)
        text_area.pack(expand=True, fill='both', padx=10, pady=10)
        
        text_area.insert(tk.END, f"> {title}\n")
        text_area.insert(tk.END, "> INIT_SCANNERS... OK\n")
        text_area.insert(tk.END, "> BYPASSING_FIREWALL... OK\n")
        text_area.insert(tk.END, "> ACCESS_GRANTED\n\n")
        
        # Typewriter effect
        def type_write(text_to_type, index=0):
            if index < len(text_to_type):
                char = text_to_type[index]
                text_area.insert(tk.END, char)
                text_area.see(tk.END)
                # Random delay for realism
                delay = random.randint(10, 50)
                top.after(delay, lambda: type_write(text_to_type, index+1))
            else:
                text_area.insert(tk.END, "\n\n> END_OF_LINE_")
        
        top.after(500, lambda: type_write(content))
        top.mainloop()

    def trace_connection(self):
        """Visualizes a network trace with random nodes."""
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.configure(background='black')
            root.attributes('-alpha', 0.9)
            root.attributes('-topmost', True)
            
            canvas = tk.Canvas(root, bg='black', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            w = root.winfo_screenwidth()
            h = root.winfo_screenheight()
            
            nodes = []
            for _ in range(20):
                nodes.append((random.randint(50, w-50), random.randint(50, h-50)))
            
            # Draw lines progressively
            def draw_line(idx=0):
                if idx < len(nodes) - 1:
                    x1, y1 = nodes[idx]
                    x2, y2 = nodes[idx+1]
                    canvas.create_line(x1, y1, x2, y2, fill='#00FF00', width=2)
                    canvas.create_oval(x1-5, y1-5, x1+5, y1+5, fill='#00FF00')
                    canvas.create_text(x1, y1-20, text=f"NODE_{random.randint(100,999)}", fill='#00FF00', font=('Courier', 10))
                    root.after(200, lambda: draw_line(idx+1))
                else:
                    target = nodes[-1]
                    canvas.create_text(target[0], target[1]-20, text="TARGET_LOCATED", fill='red', font=('Courier', 20, 'bold'))
                    root.after(2000, root.destroy)
            
            draw_line()
            root.mainloop()
        except:
            pass

    def system_override(self):
        """Flashes Access Denied then Access Granted."""
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.configure(background='black')
            root.attributes('-topmost', True)
            
            lbl = tk.Label(root, text="ACCESS DENIED", fg="red", bg="black", font=("Courier", 80, "bold"))
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            def grant_access():
                lbl.config(text="ACCESS GRANTED", fg="#00FF00")
                root.after(2000, root.destroy)
            
            root.after(1500, grant_access)
            root.mainloop()
        except:
            pass
            
    def brute_force(self):
        """Simulates rapid code breaking."""
        try:
            root = tk.Tk()
            root.geometry("400x200")
            root.configure(background='black')
            root.attributes('-topmost', True)
            root.title("DECRYPTING...")
            
            lbl = tk.Label(root, text="00000000", fg="#00FF00", bg="black", font=("Courier", 40, "bold"))
            lbl.pack(expand=True)
            
            def roll():
                chars = "0123456789ABCDEF"
                code = "".join(random.choice(chars) for _ in range(8))
                lbl.config(text=code)
                if random.random() > 0.95: # 5% chance to stop
                    lbl.config(fg="white", text="MATCH_FOUND")
                    root.after(2000, root.destroy)
                else:
                    root.after(50, roll)
            
            roll()
            root.mainloop()
        except:
            pass

    def satellite_link(self):
        """Simulates establishing a satellite uplink."""
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.configure(background='black', alpha=0.8)
            root.attributes('-topmost', True)
            
            canvas = tk.Canvas(root, bg='black', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
            
            cx, cy = w/2, h/2
            
            def animate_dish(angle=0):
                canvas.delete("all")
                canvas.create_text(cx, cy+200, text="ESTABLISHING UPLINK...", fill="cyan", font=("Courier", 20))
                
                # Simple dish rep
                import math
                rad = 100
                x = cx + rad * math.cos(math.radians(angle))
                y = cy + rad * math.sin(math.radians(angle))
                
                canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill="white")
                canvas.create_line(cx, cy, x, y, fill="cyan", width=3)
                canvas.create_oval(cx-rad, cy-rad, cx+rad, cy+rad, outline="cyan", dash=(4, 4))
                
                root.after(50, lambda: animate_dish((angle+5)%360))
                
                if angle > 350: # One full rotation then close? No, let it spin a bit
                    pass 
            
            # Auto close after 4 seconds
            root.after(4000, root.destroy)
            animate_dish()
            root.mainloop()
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        effect = sys.argv[1]
        visuals = JarvisVisuals()
        
        if effect == "hud":
            visuals.canvas_hud()
        elif effect == "arc":
            visuals.arc_reactor_pulse()
        elif effect == "fly":
            visuals.iron_man_fly()
        elif effect == "terminal" and len(sys.argv) >= 4:
            # sys.argv[2] is title (b64), sys.argv[3] is content (b64)
            visuals.hacker_terminal(sys.argv[2], sys.argv[3])
        elif effect == "trace":
            visuals.trace_connection()
        elif effect == "override":
            visuals.system_override()
        elif effect == "brute":
            visuals.brute_force()
        elif effect == "satellite":
            visuals.satellite_link()
