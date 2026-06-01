import os
import sys
import random
from PySide6.QtWidgets import QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QPixmap, QTransform

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SPRITE_DIR = os.path.join(BASE_DIR, "sprites")
RUN_DIR = os.path.join(BASE_DIR, "sprites", "run_frames")
WALK_DIR = os.path.join(BASE_DIR, "sprites", "walk_frames")
DANCE_DIR = os.path.join(BASE_DIR, "sprites", "dance_frames")
IDLE_FRAMES_DIR = os.path.join(BASE_DIR, "sprites", "idle_frames")
GREET_DIR = os.path.join(BASE_DIR, "sprites", "greet_frames")
SPEECHLESS_DIR = os.path.join(BASE_DIR, "sprites", "speechless_frames")

class CharacterWidget(QLabel):
    escaped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setAlignment(Qt.AlignCenter)

        self.idle_display_size = 300
        self.run_display_size = 300
        self.walk_display_size = 300
        self.dance_display_size = 300
        self.greet_display_size = 300
        self.speechless_display_size = 300

        self.idle_anim_frames = self.load_idle_animation_frames()
        self.run_frames = self.load_run_frames()
        self.walk_frames = self.load_walk_frames()
        self.dance_frames = self.load_dance_frames()
        self.greet_frames = self.load_greet_frames()
        self.speechless_frames = self.load_speechless_frames()

        self.run_frames_flipped = self._flip_frames(self.run_frames)
        self.walk_frames_flipped = self._flip_frames(self.walk_frames)
        self.dance_frames_flipped = self._flip_frames(self.dance_frames)
        self.greet_frames_flipped = self._flip_frames(self.greet_frames)
        self.speechless_frames_flipped = self._flip_frames(self.speechless_frames)

        self.idle_frame_index = 0
        self.current_pixmap = self.idle_anim_frames[0] if self.idle_anim_frames else QPixmap()
        self.facing_right = True

        self.state = "idle"
        self.move_frame_index = 0
        self.move_direction = 1
        self.move_target_x = 0
        self.dance_loop_count = 0
        self.greet_loop_count = 0
        self.speechless_loop_count = 0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_move_frame)

        self.idle_anim_timer = QTimer(self)
        self.idle_anim_timer.timeout.connect(self.update_idle_frame)

        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.on_idle_timeout)

        self.start_idle_animation()
        self.schedule_next_idle()

    def _flip_frames(self, frames):
        result = []
        for pix in frames:
            result.append(pix.transformed(QTransform().scale(-1, 1)))
        return result

    def load_idle_animation_frames(self):
        frames = []
        if os.path.isdir(IDLE_FRAMES_DIR):
            files = sorted([f for f in os.listdir(IDLE_FRAMES_DIR) if f.endswith(".png")])
            for fname in files:
                path = os.path.join(IDLE_FRAMES_DIR, fname)
                if os.path.exists(path):
                    pix = QPixmap(path)
                    frames.append(pix.scaled(self.idle_display_size, self.idle_display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if not frames:
            frames.append(QPixmap(self.idle_display_size, self.idle_display_size))
            frames[0].fill(Qt.transparent)
        return frames

    def load_run_frames(self):
        frames = []
        if os.path.isdir(RUN_DIR):
            files = sorted([f for f in os.listdir(RUN_DIR) if f.endswith(".png")])
            for fname in files[9:]:
                path = os.path.join(RUN_DIR, fname)
                if os.path.exists(path):
                    pix = QPixmap(path)
                    frames.append(pix.scaled(self.run_display_size, self.run_display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if not frames:
            frames.append(QPixmap(self.run_display_size, self.run_display_size))
            frames[0].fill(Qt.transparent)
        return frames

    def load_walk_frames(self):
        frames = []
        if os.path.isdir(WALK_DIR):
            files = sorted([f for f in os.listdir(WALK_DIR) if f.endswith(".png")])
            for fname in files:
                path = os.path.join(WALK_DIR, fname)
                if os.path.exists(path):
                    pix = QPixmap(path)
                    frames.append(pix.scaled(self.walk_display_size, self.walk_display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if not frames:
            frames.append(QPixmap(self.walk_display_size, self.walk_display_size))
            frames[0].fill(Qt.transparent)
        return frames

    def load_dance_frames(self):
        frames = []
        if os.path.isdir(DANCE_DIR):
            files = sorted([f for f in os.listdir(DANCE_DIR) if f.endswith(".png")])
            for fname in files:
                path = os.path.join(DANCE_DIR, fname)
                if os.path.exists(path):
                    pix = QPixmap(path)
                    frames.append(pix.scaled(self.dance_display_size, self.dance_display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if not frames:
            frames.append(QPixmap(self.dance_display_size, self.dance_display_size))
            frames[0].fill(Qt.transparent)
        return frames

    def load_greet_frames(self):
        frames = []
        if os.path.isdir(GREET_DIR):
            files = sorted([f for f in os.listdir(GREET_DIR) if f.endswith(".png")])
            for fname in files:
                path = os.path.join(GREET_DIR, fname)
                if os.path.exists(path):
                    pix = QPixmap(path)
                    frames.append(pix.scaled(self.greet_display_size, self.greet_display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if not frames:
            frames.append(QPixmap(self.greet_display_size, self.greet_display_size))
            frames[0].fill(Qt.transparent)
        return frames

    def load_speechless_frames(self):
        frames = []
        if os.path.isdir(SPEECHLESS_DIR):
            files = sorted([f for f in os.listdir(SPEECHLESS_DIR) if f.endswith(".png")])
            for fname in files:
                path = os.path.join(SPEECHLESS_DIR, fname)
                if os.path.exists(path):
                    pix = QPixmap(path)
                    frames.append(pix.scaled(self.speechless_display_size, self.speechless_display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if not frames:
            frames.append(QPixmap(self.speechless_display_size, self.speechless_display_size))
            frames[0].fill(Qt.transparent)
        return frames

    def update_display(self):
        self.setPixmap(self.current_pixmap)

    def start_idle_animation(self):
        self.state = "idle"
        self.anim_timer.stop()
        self.idle_anim_timer.start(200)

    def update_idle_frame(self):
        if self.state != "idle":
            return
        if self.idle_anim_frames:
            self.idle_frame_index = (self.idle_frame_index + 1) % len(self.idle_anim_frames)
            self.current_pixmap = self.idle_anim_frames[self.idle_frame_index]
            self.update_display()

    def schedule_next_idle(self):
        self.idle_timer.stop()
        duration = random.randint(8000, 25000)
        self.idle_timer.start(duration)

    def on_idle_timeout(self):
        if self.state != "idle":
            return
        parent = self.parent()
        if not parent:
            self.schedule_next_idle()
            return
        roll = random.random()
        if roll < 0.35:
            self.start_walking()
        elif roll < 0.70:
            self.start_running()
        else:
            self.start_dancing()

    def start_greeting(self):
        parent = self.parent()
        if not parent:
            return
        self.idle_anim_timer.stop()
        self.state = "greeting"
        self.move_frame_index = 0
        self.greet_loop_count = 0
        self.anim_timer.start(60)

    def start_walking(self):
        parent = self.parent()
        screen = QApplication.primaryScreen()
        if not parent or not screen:
            self.schedule_next_idle()
            return

        screen_geo = screen.availableGeometry()
        max_x = screen_geo.width() - parent.width()
        current_x = parent.x()

        distance = random.randint(100, 280)
        direction = random.choice([-1, 1])
        target_x = current_x + direction * distance
        target_x = max(20, min(target_x, max_x - 20))

        self.move_target_x = target_x
        self.move_direction = 1 if target_x > current_x else -1
        self.facing_right = self.move_direction > 0

        self.idle_anim_timer.stop()
        self.state = "walking"
        self.move_frame_index = 0
        self.anim_timer.start(60)

    def start_running(self):
        parent = self.parent()
        screen = QApplication.primaryScreen()
        if not parent or not screen:
            self.schedule_next_idle()
            return

        screen_geo = screen.availableGeometry()
        max_x = screen_geo.width() - parent.width()
        current_x = parent.x()

        distance = random.randint(150, 350)
        direction = random.choice([-1, 1])
        target_x = current_x + direction * distance
        target_x = max(20, min(target_x, max_x - 20))

        self.move_target_x = target_x
        self.move_direction = 1 if target_x > current_x else -1
        self.facing_right = self.move_direction > 0

        self.idle_anim_timer.stop()
        self.state = "running"
        self.move_frame_index = 0
        self.anim_timer.start(30)

    def start_dancing(self):
        parent = self.parent()
        if not parent:
            self.schedule_next_idle()
            return

        self.idle_anim_timer.stop()
        self.state = "dancing"
        self.move_frame_index = 0
        self.dance_loop_count = 0
        self.anim_timer.start(100)

    def start_speechless(self):
        parent = self.parent()
        if not parent:
            return
        self.idle_anim_timer.stop()
        self.state = "speechless"
        self.move_frame_index = 0
        self.speechless_loop_count = 0
        self.anim_timer.start(200)

    def start_walk_away(self):
        parent = self.parent()
        screen = QApplication.primaryScreen()
        if not parent or not screen:
            return
        screen_geo = screen.availableGeometry()
        max_x = screen_geo.width() - parent.width()
        current_x = parent.x()
        direction = self._pick_escape_direction(current_x, max_x)
        target_x = max_x if direction > 0 else 0
        limited = min(350, abs(target_x - current_x))
        actual_target = current_x + direction * limited
        self.move_target_x = actual_target
        self.move_direction = direction
        self.facing_right = direction > 0
        self.idle_anim_timer.stop()
        self.state = "walk_away"
        self.move_frame_index = 0
        self.anim_timer.start(60)

    def start_run_away(self):
        parent = self.parent()
        screen = QApplication.primaryScreen()
        if not parent or not screen:
            return
        screen_geo = screen.availableGeometry()
        max_x = screen_geo.width() - parent.width()
        current_x = parent.x()
        direction = self._pick_escape_direction(current_x, max_x)
        target_x = max_x if direction > 0 else 0
        limited = min(500, abs(target_x - current_x))
        actual_target = current_x + direction * limited
        self.move_target_x = actual_target
        self.move_direction = direction
        self.facing_right = direction > 0
        self.idle_anim_timer.stop()
        self.state = "run_away"
        self.move_frame_index = 0
        self.anim_timer.start(30)

    def _pick_escape_direction(self, current_x, max_x):
        space_left = current_x
        space_right = max_x - current_x
        if abs(space_left - space_right) < 200:
            return random.choice([-1, 1])
        return -1 if space_left > space_right else 1

    def resize_pet(self, new_size):
        self.idle_display_size = new_size
        self.run_display_size = new_size
        self.walk_display_size = new_size
        self.dance_display_size = new_size
        self.greet_display_size = new_size
        self.speechless_display_size = new_size
        self.idle_anim_frames = self.load_idle_animation_frames()
        self.run_frames = self.load_run_frames()
        self.walk_frames = self.load_walk_frames()
        self.dance_frames = self.load_dance_frames()
        self.greet_frames = self.load_greet_frames()
        self.speechless_frames = self.load_speechless_frames()
        self.run_frames_flipped = self._flip_frames(self.run_frames)
        self.walk_frames_flipped = self._flip_frames(self.walk_frames)
        self.dance_frames_flipped = self._flip_frames(self.dance_frames)
        self.greet_frames_flipped = self._flip_frames(self.greet_frames)
        self.speechless_frames_flipped = self._flip_frames(self.speechless_frames)
        self.idle_frame_index = 0
        if self.idle_anim_frames:
            self.current_pixmap = self.idle_anim_frames[0]
        self.update_display()
        self.start_idle_animation()

    def update_move_frame(self):
        parent = self.parent()
        if not parent:
            self.resume_idle()
            return

        if self.state == "greeting":
            frames = self.greet_frames
            flipped = self.greet_frames_flipped
            if frames:
                self.move_frame_index = (self.move_frame_index + 1) % len(frames)
                if self.move_frame_index == 0:
                    self.greet_loop_count += 1
                pix = flipped[self.move_frame_index] if not self.facing_right else frames[self.move_frame_index]
                self.current_pixmap = pix
                self.update_display()
            if self.greet_loop_count >= 2:
                self.resume_idle()
            return

        if self.state == "dancing":
            frames = self.dance_frames
            flipped = self.dance_frames_flipped
            if frames:
                self.move_frame_index = (self.move_frame_index + 1) % len(frames)
                if self.move_frame_index == 0:
                    self.dance_loop_count += 1
                pix = flipped[self.move_frame_index] if not self.facing_right else frames[self.move_frame_index]
                self.current_pixmap = pix
                self.update_display()
            if self.dance_loop_count >= 3:
                self.resume_idle()
            return

        if self.state == "speechless":
            frames = self.speechless_frames
            flipped = self.speechless_frames_flipped
            if frames:
                self.move_frame_index = (self.move_frame_index + 1) % len(frames)
                if self.move_frame_index == 0:
                    self.speechless_loop_count += 1
                pix = flipped[self.move_frame_index] if not self.facing_right else frames[self.move_frame_index]
                self.current_pixmap = pix
                self.update_display()
            if self.speechless_loop_count >= 4:
                self.resume_idle()
            return

        current_x = parent.x()
        speed = 4 if self.state in ("running", "run_away") else 2
        step = speed * self.move_direction
        new_x = current_x + step

        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            max_x = screen_geo.width() - parent.width()
            new_x = max(0, min(new_x, max_x))

        parent.move(new_x, parent.y())

        if self.state in ("walk_away", "run_away"):
            frames = self.run_frames if self.state == "run_away" else self.walk_frames
            flipped = self.run_frames_flipped if self.state == "run_away" else self.walk_frames_flipped
        else:
            frames = self.run_frames if self.state == "running" else self.walk_frames
            flipped = self.run_frames_flipped if self.state == "running" else self.walk_frames_flipped
        if frames:
            self.move_frame_index = (self.move_frame_index + 1) % len(frames)
            should_flip = self.facing_right if self.state in ("walking", "walk_away") else not self.facing_right
            pix = flipped[self.move_frame_index] if should_flip else frames[self.move_frame_index]
            self.current_pixmap = pix
            self.update_display()

        if abs(new_x - self.move_target_x) < speed or new_x <= 0 or new_x >= max_x:
            if self.state in ("walk_away", "run_away"):
                self.resume_idle()
                self.escaped.emit()
            else:
                self.resume_idle()

    def stop_walking(self):
        self.anim_timer.stop()
        self.resume_idle()

    def resume_idle(self):
        self.anim_timer.stop()
        self.start_idle_animation()
        self.schedule_next_idle()