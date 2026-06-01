import json
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class KnowledgeBase:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = BASE_DIR
        self.style_profile = None
        self.messages = []
        self.loaded = False
        self._load(data_dir)

    def _load(self, data_dir):
        style_path = os.path.join(data_dir, "style_profile.json")
        msg_path = os.path.join(data_dir, "messages.json")
        if os.path.exists(style_path) and os.path.exists(msg_path):
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    self.style_profile = json.load(f)
                with open(msg_path, "r", encoding="utf-8") as f:
                    self.messages = json.load(f)
                self.loaded = True
            except (json.JSONDecodeError, IOError):
                self.loaded = False

    def get_style_description(self):
        if self.style_profile:
            return self.style_profile.get("style_description", "")
        return ""

    def sample_random(self, n=3):
        if not self.messages:
            return []
        good = [m for m in self.messages if len(m["content"]) >= 6]
        if len(good) < n:
            good = [m for m in self.messages if len(m["content"]) >= 3]
        if not good:
            return random.sample(self.messages, min(n, len(self.messages)))
        return random.sample(good, min(n, len(good)))

    def is_available(self):
        return self.loaded and len(self.messages) > 0

    def stats(self):
        if not self.loaded:
            return {"loaded": False}
        return {
            "loaded": True,
            "total_messages": len(self.messages),
            "avg_length": self.style_profile.get("avg_length", 0),
            "common_phrases": self.style_profile.get("common_phrases", []),
        }