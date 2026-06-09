import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

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
    "theme": "dark",  # dark, light, cyberpunk, custom
    "custom_bg": "#1e1e2e",
    "custom_fg": "#cdd6f4",
    "font_size": 12,
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
