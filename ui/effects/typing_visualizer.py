from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QTransform
import random
import math
import time

class TypingVisualizer(QLabel):
    def __init__(self, parent, input_box):
        super().__init__(parent)
        self.input_box = input_box
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.bursts = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        self.start_time = time.time()
        self.update_position()

    def trigger_burst(self):
        base_radius = random.randint(3, 10)

        def spawn_single_particle():
            color = QColor(0, 110, 255)
            color.setHsv(color.hue() + random.randint(-15, 15), color.saturation(), color.value())
            self.bursts.append({
                'color': color,
                'alpha': random.uniform(0.55, 0.95),  # brighter overall
                'lifetime': 20,
                'x': random.uniform(0, self.width()),
                'y': random.uniform(0, self.height()),
                'radius': base_radius,
                'dx': random.uniform(-0.6, 0.6),  # subtle horizontal drift
                'dy': random.uniform(-1.2, -0.4),  # more upward drift
                'osc_phase': random.uniform(0, 2 * math.pi),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-5, 5),
                'trail': []
            })

        spawn_single_particle()

        if base_radius <= 5:
            extra_particles = int((10 - base_radius) * random.uniform(1.2, 2.5))  # slightly more ash
            for _ in range(extra_particles):
                spawn_single_particle()

    def resizeEvent(self, event):
        self.update_position()
        super().resizeEvent(event)

    def update_position(self):
        input_geo = self.input_box.geometry()
        self.setGeometry(input_geo.left(), input_geo.top() - 50, input_geo.width(), 50)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        current_time = time.time() - self.start_time
        frequency = 4.0
        amplitude = 0.3

        for burst in self.bursts:
            # --- Trail Rendering ---
            for i, (tx, ty, tradius, talpha) in enumerate(burst['trail']):
                trail_color = QColor(burst['color'])
                trail_color.setAlphaF(talpha * 0.3)  # lighter alpha for trails
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(trail_color)
                painter.drawEllipse(int(tx), int(ty), int(tradius), int(tradius))

            # --- Main Particle ---
            color = QColor(burst['color'])
            color.setAlphaF(burst['alpha'])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)

            osc_x = amplitude * math.sin(2 * math.pi * frequency * current_time + burst['osc_phase'])
            osc_y = amplitude * math.cos(2 * math.pi * frequency * current_time + burst['osc_phase'])

            x = burst['x'] + osc_x
            y = burst['y'] + osc_y

            transform = QTransform()
            center_x = x + burst['radius'] / 2
            center_y = y + burst['radius'] / 2
            transform.translate(center_x, center_y)
            transform.rotate(burst['rotation'])
            transform.translate(-center_x, -center_y)

            painter.setTransform(transform)

            painter.drawEllipse(int(x), int(y), int(burst['radius']), int(burst['radius']))
            painter.resetTransform()

            # Update trail history
            burst['trail'].append((x, y, burst['radius'], burst['alpha']))
            if len(burst['trail']) > 6:
                burst['trail'].pop(0)

            if random.random() < 0.05:  # 5% chance
                burst['dy'] = random.uniform(0.2, 0.6)  # drifting downward

        # Update motion
        for burst in self.bursts:
            burst['x'] += burst['dx']
            burst['y'] += burst['dy']
            burst['rotation'] += burst['rotation_speed']
            burst['lifetime'] -= 1
            burst['alpha'] = max(0.0, burst['alpha'] - 0.04)

        self.bursts = [b for b in self.bursts if b['alpha'] > 0.01 and b['lifetime'] > 0]