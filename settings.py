import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QComboBox, QPushButton, QSlider, 
    QCheckBox, QDoubleSpinBox, QFormLayout, QColorDialog,
    QMessageBox
)
from PySide6.QtGui import QFont, QColor
from libre_linkup import LibreLinkUpClient

class SettingsDialog(QDialog):
    settings_saved = Signal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle("LibreLinkUp Widget Settings")
        self.resize(450, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTabWidget::panel {
                border: 1px solid #313244;
                background-color: #181825;
            }
            QTabBar::tab {
                background-color: #1e1e2e;
                color: #a6adc8;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #181825;
                color: #cdd6f4;
                font-weight: bold;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:disabled {
                background-color: #585b70;
                color: #a6adc8;
            }
        """)
        
        self.init_ui()
        self.load_values()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Tab 1: Account
        self.tab_account = QWidget()
        self.init_account_tab()
        self.tabs.addTab(self.tab_account, "Account")

        # Tab 2: Style
        self.tab_style = QWidget()
        self.init_style_tab()
        self.tabs.addTab(self.tab_style, "Style")

        # Tab 3: Alerts
        self.tab_alerts = QWidget()
        self.init_alerts_tab()
        self.tabs.addTab(self.tab_alerts, "Alerts")

        # Save Button
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.btn_save)

    def init_account_tab(self):
        layout = QVBoxLayout(self.tab_account)
        form = QFormLayout()
        
        self.in_email = QLineEdit()
        self.in_email.setPlaceholderText("follower@email.com")
        form.addRow("Email:", self.in_email)
        
        self.in_password = QLineEdit()
        self.in_password.setEchoMode(QLineEdit.Password)
        self.in_password.setPlaceholderText("Password")
        form.addRow("Password:", self.in_password)
        
        self.in_region = QComboBox()
        self.in_region.addItems(["US", "EU", "EU2", "DE", "JP", "AP", "AU", "AE"])
        form.addRow("Server Region:", self.in_region)
        
        self.btn_test = QPushButton("Connect & Fetch Patients")
        self.btn_test.clicked.connect(self.connect_api)
        form.addRow("", self.btn_test)
        
        self.in_patient = QComboBox()
        form.addRow("Target Patient:", self.in_patient)
        
        layout.addLayout(form)
        layout.addStretch()

    def init_style_tab(self):
        layout = QVBoxLayout(self.tab_style)
        form = QFormLayout()

        self.in_is_widget = QCheckBox("Show as Desktop Widget (Transparent, Frameless)")
        form.addRow("", self.in_is_widget)

        self.in_always_on_top = QCheckBox("Always on Top")
        form.addRow("", self.in_always_on_top)

        self.in_opacity = QSlider(Qt.Horizontal)
        self.in_opacity.setRange(10, 100)
        form.addRow("Widget Opacity:", self.in_opacity)

        self.btn_bg = QPushButton()
        self.btn_bg.setFixedWidth(56)
        self.btn_bg.setStyleSheet("background-color: #1e1e2e; border: 1px solid #45475a;")
        self.btn_bg.clicked.connect(self.pick_bg)
        form.addRow("Background:", self.btn_bg)

        self.in_font_size = QSlider(Qt.Horizontal)
        self.in_font_size.setRange(10, 24)
        form.addRow("Font Base Size:", self.in_font_size)

        self.in_text_fx = QComboBox()
        self.in_text_fx.addItems(["None", "Text Shadow", "Text Outline"])
        form.addRow("Text Effect:", self.in_text_fx)

        self.in_width = QDoubleSpinBox()
        self.in_width.setRange(150, 600)
        self.in_width.setDecimals(0)
        form.addRow("Width (px):", self.in_width)

        self.in_height = QDoubleSpinBox()
        self.in_height.setRange(100, 400)
        self.in_height.setDecimals(0)
        form.addRow("Height (px):", self.in_height)

        layout.addLayout(form)

        # Element color + opacity controls
        elems_layout = QVBoxLayout()
        ttl = QLabel("Element Colors")
        ttl.setStyleSheet("font-weight: bold; color: #a6adc8; padding-top: 6px;")
        elems_layout.addWidget(ttl)

        self.color_values = {}
        self.color_buttons = {}
        self.color_sliders = {}

        self._add_color_row(elems_layout, "Name of Patient", "opacity_patient", [("", "patient")])
        self._add_color_row(elems_layout, "Low/High Glucose", "opacity_out", [("Low", "low"), ("High", "high")])
        self._add_color_row(elems_layout, "In-Range Glucose", "opacity_normal", [("", "normal")])
        self._add_color_row(elems_layout, "Updated", "opacity_updated", [("", "updated")])
        self._add_color_row(elems_layout, "Misc. Text", "opacity_misc", [("", "misc")])

        layout.addLayout(elems_layout)
        layout.addStretch()

    def _add_color_row(self, layout, label, slider_key, color_specs):
        """Add a row: label + one/two color buttons + one opacity slider."""
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(120)
        row.addWidget(lbl)

        for btn_text, key in color_specs:
            btn = QPushButton(btn_text)
            if btn_text:
                btn.setFixedWidth(48)
            else:
                btn.setFixedWidth(32)
            btn.setStyleSheet("background-color: #cdd6f4; border: 1px solid #45475a;")
            btn.clicked.connect(lambda checked=False, k=key, b=btn: self.pick_element_color(k, b))
            row.addWidget(btn)
            self.color_buttons[key] = btn

        row.addStretch()

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setFixedWidth(120)
        slider.valueChanged.connect(lambda v, k=slider_key: self.update_opacity_label(k, v))
        row.addWidget(slider)
        self.color_sliders[slider_key] = slider

        # Little opacity % indicator
        indicator = QLabel("100%")
        indicator.setFixedWidth(38)
        self.opacity_labels = getattr(self, "opacity_labels", {})
        self.opacity_labels[slider_key] = indicator
        row.addWidget(indicator)

        layout.addLayout(row)

    def update_opacity_label(self, slider_key, val):
        ind = self.opacity_labels.get(slider_key)
        if ind:
            ind.setText(f"{val}%")

    def pick_element_color(self, key, btn):
        current = self.color_values.get(key, "#cdd6f4")
        col = QColorDialog.getColor(QColor(current), self, "Select Color")
        if col.isValid():
            self.color_values[key] = col.name()
            btn.setStyleSheet(
                f"background-color: {col.name()}; color: #11111b; border: 1px solid #45475a;"
            )

    def init_alerts_tab(self):
        layout = QVBoxLayout(self.tab_alerts)
        form = QFormLayout()
        
        self.in_unit = QComboBox()
        self.in_unit.addItems(["mg/dL", "mmol/L"])
        self.in_unit.currentTextChanged.connect(self.update_unit_labels)
        form.addRow("Glucose Unit:", self.in_unit)
        
        self.in_high = QDoubleSpinBox()
        self.in_high.setRange(100, 350)
        self.in_high.setDecimals(1)
        self.lbl_high = QLabel("High Alarm Limit:")
        form.addRow(self.lbl_high, self.in_high)
        
        self.in_low = QDoubleSpinBox()
        self.in_low.setRange(40, 120)
        self.in_low.setDecimals(1)
        self.lbl_low = QLabel("Low Alarm Limit:")
        form.addRow(self.lbl_low, self.in_low)
        
        self.in_notify = QCheckBox("Enable Windows Push Notifications")
        form.addRow("", self.in_notify)
        
        self.in_startup = QCheckBox("Launch App on Windows Startup")
        form.addRow("", self.in_startup)
        
        layout.addLayout(form)
        layout.addStretch()

    def pick_bg(self):
        current = self.color_values.get("bg", "#1e1e2e")
        col = QColorDialog.getColor(QColor(current), self, "Select Background Color")
        if col.isValid():
            self.color_values["bg"] = col.name()
            self.btn_bg.setStyleSheet(
                f"background-color: {col.name()}; border: 1px solid #45475a;"
            )

    def update_unit_labels(self, unit):
        # Update spinbox limits and defaults based on unit
        if unit == "mmol/L":
            self.in_high.setRange(5.5, 19.4)
            self.in_low.setRange(2.2, 6.7)
            self.in_high.setValue(10.0) # ~180 mg/dL
            self.in_low.setValue(3.9)   # ~70 mg/dL
        else:
            self.in_high.setRange(100, 350)
            self.in_low.setRange(40, 120)
            self.in_high.setValue(180)
            self.in_low.setValue(70)

    def load_values(self):
        cfg = self.config_manager
        
        self.in_email.setText(cfg.get("email"))
        self.in_password.setText(cfg.get("password"))
        self.in_region.setCurrentText(cfg.get("region").upper())
        
        if cfg.get("patient_id"):
            self.in_patient.addItem(cfg.get("patient_name") or "Saved Connection", cfg.get("patient_id"))
            
        self.in_is_widget.setChecked(cfg.get("is_widget"))
        self.in_always_on_top.setChecked(cfg.get("always_on_top"))
        self.in_opacity.setValue(int(cfg.get("opacity") * 100))

        self.color_values["bg"] = cfg.get("bg_color")
        self.btn_bg.setStyleSheet(
            f"background-color: {cfg.get('bg_color')}; border: 1px solid #45475a;"
        )

        # Element colors
        color_keys = {
            "patient": "color_patient",
            "high": "color_high",
            "low": "color_low",
            "normal": "color_normal",
            "updated": "color_updated",
            "misc": "color_misc",
        }
        for key, cfg_key in color_keys.items():
            col = cfg.get(cfg_key)
            self.color_values[key] = col
            btn = self.color_buttons.get(key)
            if btn:
                btn.setStyleSheet(
                    f"background-color: {col}; color: #11111b; border: 1px solid #45475a;"
                )

        # Opacities
        for slider_key, opacity_key in [
            ("opacity_patient", "opacity_patient"),
            ("opacity_out", "opacity_out"),
            ("opacity_normal", "opacity_normal"),
            ("opacity_updated", "opacity_updated"),
            ("opacity_misc", "opacity_misc"),
        ]:
            slider = self.color_sliders.get(slider_key)
            if slider:
                val = cfg.get(opacity_key)
                slider.setValue(val)
                self.update_opacity_label(slider_key, val)

        self.in_font_size.setValue(cfg.get("font_size"))
        fx = cfg.get("text_fx", "none")
        self.in_text_fx.setCurrentText({"none": "None", "shadow": "Text Shadow", "outline": "Text Outline"}.get(fx, "None"))
        self.in_width.setValue(cfg.get("width"))
        self.in_height.setValue(cfg.get("height"))
        
        # Load Unit and Thresholds
        unit = cfg.get("unit")
        self.in_unit.setCurrentText(unit)
        if unit == "mmol/L":
            # Convert values if saved in mg/dL
            h = cfg.get("high_threshold")
            l = cfg.get("low_threshold")
            # Convert thresholds if stored as mg/dL
            self.in_high.setValue(h / 18.0182 if h > 30 else h)
            self.in_low.setValue(l / 18.0182 if l > 30 else l)
        else:
            self.in_high.setValue(cfg.get("high_threshold"))
            self.in_low.setValue(cfg.get("low_threshold"))
            
        self.in_notify.setChecked(cfg.get("notifications_enabled"))
        self.in_startup.setChecked(cfg.get("startup_enabled"))

    def connect_api(self):
        self.btn_test.setEnabled(False)
        self.btn_test.setText("Connecting...")
        
        email = self.in_email.text().strip()
        pwd = self.in_password.text().strip()
        region = self.in_region.currentText().lower()
        
        if not email or not pwd:
            # Connect in Mock mode
            self.in_patient.clear()
            self.in_patient.addItem("Demo Patient (Offline)", "mock-patient-1")
            QMessageBox.information(self, "Offline Mode", "Running in offline demonstration mode (no credentials provided).")
            self.btn_test.setEnabled(True)
            self.btn_test.setText("Connect & Fetch Patients")
            return
            
        client = LibreLinkUpClient(email, pwd, region)
        ok, msg = client.login()
        
        if ok:
            conns = client.get_connections()
            self.in_patient.clear()
            for conn in conns:
                name = f"{conn.get('firstName', '')} {conn.get('lastName', '')}".strip() or "Patient"
                self.in_patient.addItem(name, conn.get("id"))
            
            if not conns:
                self.in_patient.addItem("No connections found", "")
                QMessageBox.warning(self, "Success", "Log in succeeded, but no follower connections were found in your LibreLinkUp account.")
            else:
                QMessageBox.information(self, "Success", "Connected successfully! Loaded patient connections.")
        else:
            QMessageBox.critical(self, "Connection Error", f"Login failed: {msg}")
            
        self.btn_test.setEnabled(True)
        self.btn_test.setText("Connect & Fetch Patients")

    def save_settings(self):
        cfg = self.config_manager
        
        cfg.set("email", self.in_email.text().strip())
        cfg.set("password", self.in_password.text().strip())
        cfg.set("region", self.in_region.currentText().lower())
        
        if self.in_patient.count() > 0:
            cfg.set("patient_id", self.in_patient.currentData())
            cfg.set("patient_name", self.in_patient.currentText())
            
        cfg.set("is_widget", self.in_is_widget.isChecked())
        cfg.set("always_on_top", self.in_always_on_top.isChecked())
        cfg.set("opacity", self.in_opacity.value() / 100.0)
        cfg.set("bg_color", self.color_values.get("bg", "#1e1e2e"))
        cfg.set("color_patient", self.color_values.get("patient", "#89b4fa"))
        cfg.set("color_high", self.color_values.get("high", "#fab387"))
        cfg.set("color_low", self.color_values.get("low", "#f38ba8"))
        cfg.set("color_normal", self.color_values.get("normal", "#a6e3a1"))
        cfg.set("color_updated", self.color_values.get("updated", "#cdd6f4"))
        cfg.set("color_misc", self.color_values.get("misc", "#cdd6f4"))
        cfg.set("opacity_patient", self.color_sliders["opacity_patient"].value())
        cfg.set("opacity_out", self.color_sliders["opacity_out"].value())
        cfg.set("opacity_normal", self.color_sliders["opacity_normal"].value())
        cfg.set("opacity_updated", self.color_sliders["opacity_updated"].value())
        cfg.set("opacity_misc", self.color_sliders["opacity_misc"].value())
        cfg.set("font_size", self.in_font_size.value())
        fx = self.in_text_fx.currentText()
        cfg.set("text_fx", {"Text Shadow": "shadow", "Text Outline": "outline"}.get(fx, "none"))
        cfg.set("width", self.in_width.value())
        cfg.set("height", self.in_height.value())
        
        unit = self.in_unit.currentText()
        cfg.set("unit", unit)
        
        high_val = self.in_high.value()
        low_val = self.in_low.value()
        
        # Save threshold values normalized to mg/dL for consistent storage
        if unit == "mmol/L":
            cfg.set("high_threshold", high_val * 18.0182)
            cfg.set("low_threshold", low_val * 18.0182)
        else:
            cfg.set("high_threshold", high_val)
            cfg.set("low_threshold", low_val)
            
        cfg.set("notifications_enabled", self.in_notify.isChecked())
        cfg.set("startup_enabled", self.in_startup.isChecked())
        
        # Trigger layout and behavior changes in widget
        self.settings_saved.emit()
        self.accept()
