import os
import sys
import json

APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

DEFAULT_CONFIG = {
    # Account Settings
    "email": "",
    "password": "",
    "region": "us",  # us, eu, de, jp, ap, etc.
    "patient_id": "",
    "patient_name": "",
    
    # Widget Layout & Theme
    "x": 100,
    "y": 100,
    "width": 220,
    "height": 130,
    "opacity": 0.9,
    "bg_color": "#1e1e2e",
    "color_patient": "#89b4fa",
    "color_high": "#fab387",
    "color_low": "#f38ba8",
    "color_normal": "#a6e3a1",
    "color_updated": "#cdd6f4",
    "color_misc": "#cdd6f4",
    "opacity_patient": 100,
    "opacity_out": 100,
    "opacity_normal": 100,
    "opacity_updated": 60,
    "opacity_misc": 100,
    "font_size": 12,
    "text_fx": "none",  # none, shadow, outline
    "always_on_top": True,
    "is_widget": True,  # True = frameless transparent widget, False = normal window
    
    # Alerts and Snoozing
    "high_threshold": 180.0,
    "low_threshold": 70.0,
    "notifications_enabled": True,
    "snoozed_high": False,
    "snoozed_low": False,
    "unit": "mg/dL",  # mg/dL or mmol/L
    
    # System Settings
    "startup_enabled": False
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    # Merge loaded keys to support updates
                    for k, v in data.items():
                        self.config[k] = v
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
