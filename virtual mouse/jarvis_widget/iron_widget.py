import sys
import os
import math
import psutil
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QLinearGradient, QPixmap, QPainterPath

# --- Configuration ---
WIDGET_WIDTH = 350
WIDGET_HEIGHT = 600
UPDATE_INTERVAL_STATS = 1000  # ms
UPDATE_INTERVAL_ANIM = 30     # ms (~30 FPS sufficient for this)
ALWAYS_ON_TOP = True

# Colors (Superior Iron Man / Symbiote)
COLOR_SILVER = QColor(220, 220, 230)
COLOR_CHROME = QColor(200, 200, 210)
COLOR_CYAN_GLOW = QColor(0, 255, 255)
COLOR_ORANGE_GLOW = QColor(255, 100, 0) # Accents
COLOR_HUD_BG = QColor(0, 20, 30, 150) # Dark transparent background

class IronManWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        if ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        self.resize(WIDGET_WIDTH, WIDGET_HEIGHT)
        
        # Center initially
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

        # --- Load Assets ---
        image_path = os.path.join(os.path.dirname(__file__), "superior_iron_man.png")
        self.character_pixmap = None
        if os.path.exists(image_path):
            pix = QPixmap(image_path)
            if not pix.isNull():
                # Scale to cover the width/height nicely
                # We want it to fill the widget mostly
                self.character_pixmap = pix.scaled(
                    WIDGET_WIDTH, WIDGET_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                print(f"Warning: Failed to load image at {image_path}")
        else:
            print(f"Warning: Image not found at {image_path}")

        # --- State ---
        self.cpu_percent = 0.0
        self.ram_percent = 0.0
        
        self.anim_val = 0.0
        self.scan_line_y = 0
        
        self.hover_active = False
        self.drag_pos = None

        # --- Timers ---
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(UPDATE_INTERVAL_STATS)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(UPDATE_INTERVAL_ANIM)
        
        # Initial stats
        self.update_stats()

    def update_stats(self):
        try:
            self.cpu_percent = psutil.cpu_percent()
            self.ram_percent = psutil.virtual_memory().percent
        except Exception as e:
            print(f"Error fetching stats: {e}")

    def update_animation(self):
        # Scan line animation
        self.scan_line_y += 5
        if self.scan_line_y > WIDGET_HEIGHT:
            self.scan_line_y = 0
            
        # Pulse animation
        self.anim_val += 0.05
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # --- 1. Background Shape (Rounded Rect) ---
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 30, 30)
        
        painter.save()
        # Clip to rounded rect
        painter.setClipPath(path)
        
        # Draw dark background
        painter.fillPath(path, COLOR_HUD_BG)
        
        # --- 2. Character Image ---
        if self.character_pixmap:
            # Draw centered
            img_x = (WIDGET_WIDTH - self.character_pixmap.width()) // 2
            img_y = (WIDGET_HEIGHT - self.character_pixmap.height()) // 2
            painter.drawPixmap(img_x, img_y, self.character_pixmap)
            
        # --- 3. Scan Line Effect ---
        # Subtle horizontal line moving down
        scan_pen = QPen(QColor(0, 255, 255, 50))
        scan_pen.setWidth(2)
        painter.setPen(scan_pen)
        painter.drawLine(0, self.scan_line_y, WIDGET_WIDTH, self.scan_line_y)
        
        painter.restore() # End clipping

        # --- 4. HUD Bars (Side Overlay) ---
        # Left Bar: CPU
        self.draw_vertical_bar(painter, 10, 50, 6, WIDGET_HEIGHT - 100, self.cpu_percent, COLOR_CYAN_GLOW, "CPU")
        
        # Right Bar: RAM
        self.draw_vertical_bar(painter, WIDGET_WIDTH - 16, 50, 6, WIDGET_HEIGHT - 100, self.ram_percent, COLOR_ORANGE_GLOW, "RAM")

        # --- 5. Border Glow ---
        painter.setPen(QPen(QColor(200, 200, 255, 100), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1,1,-1,-1), 30, 30)

    def draw_vertical_bar(self, painter, x, y, w, h, percent, color, label):
        # Draw background track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        painter.drawRect(x, y, w, h)
        
        # Draw value fill (bottom up)
        fill_h = int(h * (percent / 100.0))
        fill_y = y + h - fill_h
        
        # Gradient fill
        grad = QLinearGradient(x, y+h, x, y) # Bottom to Top
        grad.setColorAt(0.0, color)
        grad.setColorAt(1.0, QColor(255, 255, 255, 200)) # Fade to white at top
        
        painter.setBrush(QBrush(grad))
        painter.drawRect(x, fill_y, w, fill_h)
        
        # Label (Rotated or simple text nearby)
        painter.save()
        painter.setPen(QColor(255, 255, 255, 200))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        # Draw label at bottom
        painter.drawText(QRectF(x - 10, y + h + 5, w + 20, 20), Qt.AlignmentFlag.AlignCenter, label)
        # Draw percent at top
        painter.drawText(QRectF(x - 10, y - 20, w + 20, 20), Qt.AlignmentFlag.AlignCenter, f"{int(percent)}")
            
        painter.restore()

    # --- Interaction ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
            
    def enterEvent(self, event):
        self.hover_active = True
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.hover_active = False
        super().leaveEvent(event)

def main():
    app = QApplication(sys.argv)
    widget = IronManWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
