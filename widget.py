import sys
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PySide6.QtGui import QFont, QColor, QPalette, QBrush, QPainter, QPen, QPainterPath, QPaintEvent, QFontMetrics

class FXLabel(QLabel):
    """QLabel that can optionally render its text with a shadow or an outline.

    Modes (set via configure()):
      - "none":    normal Qt rendering (respects the label's stylesheet color)
      - "shadow":  a soft dark offset copy of the glyphs behind the text
      - "outline": the glyphs stroked with a contrasting color
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._fill = QColor("#cdd6f4")
        self._fx = "none"
        self._fx_color = QColor("#000000")

    def configure(self, fill_hex, alpha, fx="none", fx_hex="#000000"):
        """Set the text fill color/opacity and the shadow/outline effect."""
        fill = QColor(fill_hex)
        fill.setAlpha(max(0, min(255, int(round(255 * alpha / 100.0)))))
        self._fill = fill
        self._fx = fx
        self._fx_color = QColor(fx_hex)
        # Keep the stylesheet color in sync (used for the "none" mode)
        self.setStyleSheet(f"color: rgba({fill.red()}, {fill.green()}, {fill.blue()}, {fill.alpha()});")
        self.update()

    def paintEvent(self, event: QPaintEvent):
        text = self.text()
        shown = self._elide(text)
        if self._fx == "none":
            super().paintEvent(event)
            # In "none" mode QLabel clips overflowing text; force an elided redraw
            # so long names never get cut at the right edge.
            if shown != text:
                self._paint_text(shown, Qt.ElideRight)
            return

        if not shown:
            return

        self._paint_text(shown, Qt.ElideNone)

    def _elide(self, text):
        if not text:
            return ""
        fm = QFontMetrics(self.font())
        return fm.elidedText(text, Qt.ElideRight, max(1, self.width()))

    def _paint_text(self, text, elide):
        if not text:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = self.font()
        path = QPainterPath()
        path.addText(0, 0, font, text)
        bounds = path.boundingRect()

        # Center the glyphs within the label
        cx = self.rect().center().x() - bounds.center().x()
        cy = self.rect().center().y() - bounds.center().y()
        painter.translate(cx, cy)

        if self._fx == "shadow":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 170))
            painter.save()
            painter.translate(1.5, 2.0)
            painter.drawPath(path)
            painter.restore()
            painter.setBrush(self._fill)
            painter.drawPath(path)
        elif self._fx == "outline":
            painter.setPen(QPen(self._fx_color, 1.4))
            painter.setBrush(self._fill)
            painter.drawPath(path)

        painter.end()

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
        self.title_label = FXLabel("LibreLinkUp Glucose")
        self.title_label.setFont(QFont("Outfit", 9, QFont.Bold))
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.layout.addLayout(self.header_layout)

        # Glucose Display
        self.glucose_layout = QHBoxLayout()
        
        self.value_label = FXLabel("--")
        self.value_label.setFont(QFont("Outfit", 32, QFont.Bold))
        
        self.unit_label = FXLabel("mg/dL")
        self.unit_label.setFont(QFont("Outfit", 12))
        
        self.arrow_label = FXLabel("→")
        self.arrow_label.setFont(QFont("Outfit", 28, QFont.Bold))
        
        self.glucose_layout.addWidget(self.value_label)
        self.glucose_layout.addWidget(self.unit_label)
        self.glucose_layout.addStretch()
        self.glucose_layout.addWidget(self.arrow_label)
        
        self.layout.addLayout(self.glucose_layout)

        # Footer Status Label
        self.status_label = FXLabel("Loading data...")
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

    def _rgba(self, hex_color, opacity_pct):
        """Return a QSS rgba() string from a hex color + opacity percentage."""
        c = QColor(hex_color)
        a = max(0, min(255, int(round(255 * opacity_pct / 100.0))))
        return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a})"

    def update_style(self, current_val=None):
        cfg = self.config_manager
        bg = cfg.get("bg_color")

        # Value color switches based on glucose thresholds
        if current_val is not None:
            high_t = cfg.get("high_threshold")
            low_t = cfg.get("low_threshold")
            if current_val >= high_t:
                val_color, val_alpha = cfg.get("color_high"), cfg.get("opacity_out")
            elif current_val <= low_t:
                val_color, val_alpha = cfg.get("color_low"), cfg.get("opacity_out")
            else:
                val_color, val_alpha = cfg.get("color_normal"), cfg.get("opacity_normal")
        else:
            val_color, val_alpha = cfg.get("color_normal"), cfg.get("opacity_normal")

        # Custom QSS styling
        misc_c = self._rgba(cfg.get("color_misc"), cfg.get("opacity_misc"))
        border_radius = "12px" if cfg.get("is_widget") else "0px"
        border_style = f"1px solid {misc_c}" if cfg.get("is_widget") else "none"

        self.setStyleSheet(f"""
            GlucoseWidget {{
                background-color: {bg};
                color: {misc_c};
                border: {border_style};
                border-radius: {border_radius};
            }}
            QLabel {{
                color: {misc_c};
            }}
        """)

        fx = cfg.get("text_fx", "none")

        # Apply colors to labels (each independently styled, with optional fx)
        self.title_label.configure(cfg.get("color_patient"), cfg.get("opacity_patient"), fx)
        self.value_label.configure(val_color, val_alpha, fx)
        self.arrow_label.configure(val_color, val_alpha, fx)
        self.unit_label.configure(cfg.get("color_misc"), cfg.get("opacity_misc"), fx)
        self.status_label.configure(cfg.get("color_updated"), cfg.get("opacity_updated"), fx)
        
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
