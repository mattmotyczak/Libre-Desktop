import sys
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PySide6.QtGui import QFont, QColor, QPalette, QBrush

THEMES = {
    "dark": {
        "bg": "#181825",
        "fg": "#cdd6f4",
        "title": "#89b4fa",
        "border": "#313244",
        "normal": "#a6e3a1",  # Green
        "high": "#fab387",    # Orange
        "low": "#f38ba8"      # Red
    },
    "light": {
        "bg": "#f2f2f7",
        "fg": "#1c1c1e",
        "title": "#007aff",
        "border": "#d1d1d6",
        "normal": "#34c759",  # Green
        "high": "#ff9500",    # Orange
        "low": "#ff3b30"      # Red
    },
    "cyberpunk": {
        "bg": "#000000",
        "fg": "#00ffcc",
        "title": "#ff007f",
        "border": "#00ffcc",
        "normal": "#00ffcc",
        "high": "#ffcc00",
        "low": "#ff0055"
    }
}

class GlucoseWidget(QWidget):
    open_settings_requested = Signal()
    refresh_requested = Signal()
    exit_requested = Signal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.drag_position = QPoint()
        
        self.init_ui()
        self.apply_settings()

    def init_ui(self):
        # Layout structure
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.layout.setSpacing(5)

        # Title/Header
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("LibreLinkUp Glucose")
        self.title_label.setFont(QFont("Outfit", 9, QFont.Bold))
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.layout.addLayout(self.header_layout)

        # Glucose Display
        self.glucose_layout = QHBoxLayout()
        
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont("Outfit", 32, QFont.Bold))
        
        self.unit_label = QLabel("mg/dL")
        self.unit_label.setFont(QFont("Outfit", 12))
        
        self.arrow_label = QLabel("→")
        self.arrow_label.setFont(QFont("Outfit", 28, QFont.Bold))
        
        self.glucose_layout.addWidget(self.value_label)
        self.glucose_layout.addWidget(self.unit_label)
        self.glucose_layout.addStretch()
        self.glucose_layout.addWidget(self.arrow_label)
        
        self.layout.addLayout(self.glucose_layout)

        # Footer Status Label
        self.status_label = QLabel("Loading data...")
        self.status_label.setFont(QFont("Outfit", 8))
        self.layout.addWidget(self.status_label)

    def apply_settings(self):
        cfg = self.config_manager
        
        # Window flags based on widget/normal mode
        self.setWindowFlags(Qt.Window) # Reset first
        flags = Qt.Tool
        if cfg.get("always_on_top"):
            flags |= Qt.WindowStaysOnTopHint
            
        if cfg.get("is_widget"):
            flags |= Qt.FramelessWindowHint
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        else:
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            
        self.setWindowFlags(flags)

        # Dimensions & Opacity
        self.resize(cfg.get("width"), cfg.get("height"))
        self.setWindowOpacity(cfg.get("opacity"))
        
        # Apply visual styles and colors
        self.update_style()
        
        # Restore position
        self.move(cfg.get("x"), cfg.get("y"))
        
        # Show window
        self.show()

    def update_style(self, current_val=None):
        cfg = self.config_manager
        theme_name = cfg.get("theme")
        
        if theme_name == "custom":
            bg = cfg.get("custom_bg")
            fg = cfg.get("custom_fg")
            title = fg
            border = fg
            normal_c = "#4ade80"
            high_c = "#f97316"
            low_c = "#ef4444"
        else:
            t_data = THEMES.get(theme_name, THEMES["dark"])
            bg = t_data["bg"]
            fg = t_data["fg"]
            title = t_data["title"]
            border = t_data["border"]
            normal_c = t_data["normal"]
            high_c = t_data["high"]
            low_c = t_data["low"]

        # Color-code based on value thresholds
        val_color = fg
        if current_val is not None:
            # Handle mg/dL and mmol/L conversions for thresholds
            unit = cfg.get("unit", "mg/dL")
            high_t = cfg.get("high_threshold")
            low_t = cfg.get("low_threshold")
            
            if current_val >= high_t:
                val_color = high_c
            elif current_val <= low_t:
                val_color = low_c
            else:
                val_color = normal_c

        # Custom QSS styling
        border_radius = "12px" if cfg.get("is_widget") else "0px"
        border_style = f"1px solid {border}" if cfg.get("is_widget") else "none"
        
        self.setStyleSheet(f"""
            GlucoseWidget {{
                background-color: {bg};
                color: {fg};
                border: {border_style};
                border-radius: {border_radius};
            }}
            QLabel {{
                color: {fg};
            }}
        """)
        
        # Apply colors to labels
        self.title_label.setStyleSheet(f"color: {title};")
        self.value_label.setStyleSheet(f"color: {val_color};")
        self.arrow_label.setStyleSheet(f"color: {val_color};")
        self.status_label.setStyleSheet(f"color: {fg}; opacity: 0.7;")
        
        # Update fonts
        base_size = cfg.get("font_size")
        self.title_label.setFont(QFont("Outfit", base_size - 3, QFont.Bold))
        self.value_label.setFont(QFont("Outfit", base_size + 20, QFont.Bold))
        self.unit_label.setFont(QFont("Outfit", base_size))
        self.arrow_label.setFont(QFont("Outfit", base_size + 16, QFont.Bold))
        self.status_label.setFont(QFont("Outfit", base_size - 4))

        self.unit_label.setText(cfg.get("unit", "mg/dL"))

    def update_data(self, val, trend_arrow, timestamp, is_mock=False):
        cfg = self.config_manager
        unit = cfg.get("unit", "mg/dL")
        
        # Conversion if using mmol/L
        display_val = val
        if unit == "mmol/L":
            display_val = val / 18.0182
            val_str = f"{display_val:.1f}"
        else:
            val_str = f"{int(display_val)}"

        self.value_label.setText(val_str)
        self.arrow_label.setText(trend_arrow)
        
        mock_tag = " (Demo)" if is_mock else ""
        patient_name = cfg.get("patient_name") or "Patient"
        self.title_label.setText(f"{patient_name}{mock_tag}")
        
        self.status_label.setText(f"Updated: {timestamp}")
        
        # Recalculate color
        self.update_style(val)

    # Mouse drag implementation for borderless window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.config_manager.get("is_widget"):
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.config_manager.get("is_widget"):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            # Save position coordinates
            self.config_manager.set("x", self.x())
            self.config_manager.set("y", self.y())
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_settings_requested.emit()
            event.accept()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
            }
            QMenu::item:selected {
                background-color: #89b4fa;
                color: #11111b;
            }
        """)
        
        settings_action = context_menu.addAction("Settings")
        refresh_action = context_menu.addAction("Refresh")
        context_menu.addSeparator()
        exit_action = context_menu.addAction("Exit App")
        
        action = context_menu.exec(event.globalPos())
        if action == settings_action:
            self.open_settings_requested.emit()
        elif action == refresh_action:
            self.refresh_requested.emit()
        elif action == exit_action:
            self.exit_requested.emit()
