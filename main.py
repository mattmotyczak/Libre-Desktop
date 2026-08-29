import sys
import os
import winreg
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPainter, QColor, QFont, QPixmap

from config import ConfigManager
from libre_linkup import LibreLinkUpClient
from widget import GlucoseWidget
from settings import SettingsDialog

REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_APP_NAME = "LibreLinkUpWidget"

def set_startup_registry(enabled):
    """Sets or removes the app from current user startup registry."""
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            # When frozen, launch the exe itself; otherwise use the python + script
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}"'
            else:
                cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
            winreg.SetValueEx(key, REG_APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, REG_APP_NAME)
            except FileNotFoundError:
                pass
    except Exception as e:
        print(f"Error updating startup registry: {e}")
    finally:
        winreg.CloseKey(key)

class PollerThread(QThread):
    data_received = Signal(float, str, str, bool) # val, arrow, timestamp, is_mock
    status_msg = Signal(str)

    def __init__(self, config_manager, client):
        super().__init__()
        self.config_manager = config_manager
        self.client = client
        self.running = True

    def run(self):
        # Reuse the shared, already-authenticated client so we don't hammer
        # the login endpoint (LibreLinkUp rate-limits to a few/minute -> HTTP 429).
        email = self.config_manager.get("email")
        pwd = self.config_manager.get("password")
        region = self.config_manager.get("region")

        client = self.client
        client.email = email
        client.password = pwd
        client.region = region

        while self.running:
            # Only login if we don't have a token yet
            if client.token is None:
                ok, msg = client.login()
                if ok:
                    pass
                else:
                    self.status_msg.emit(f"Auth failed: {msg}")
                    # Wait 30 seconds before retrying login
                    self.msleep(30000)
                    continue

            patient_id = self.config_manager.get("patient_id")
            if not patient_id:
                # If no patient saved, check connection list
                conns = client.get_connections()
                if conns:
                    patient_id = conns[0].get("id")
                    self.config_manager.set("patient_id", patient_id)
                    self.config_manager.set("patient_name", f"{conns[0].get('firstName', '')} {conns[0].get('lastName', '')}".strip())
                else:
                    patient_id = "mock-patient-1" # Fallback to mock

            reading = client.get_glucose_reading(patient_id)
            if reading:
                self.data_received.emit(
                    reading["value"], 
                    reading["trend_arrow"], 
                    reading["timestamp"], 
                    reading["is_mock"]
                )
            else:
                self.status_msg.emit("Reading failed")

            # Poll every 60 seconds
            for _ in range(60):
                if not self.running:
                    break
                self.msleep(1000)

    def stop(self):
        self.running = False
        self.wait()


class AppController:
    def __init__(self):
        self.config_manager = ConfigManager()
        
        # Setup widgets
        self.widget = GlucoseWidget(self.config_manager)
        self.settings_dlg = None
        
        # System Tray setup
        self.tray_icon = QSystemTrayIcon()
        self.update_tray_icon(100) # Initial tray icon with placeholder value 100
        
        self.tray_menu = QMenu()
        self.act_show_hide = self.tray_menu.addAction("Hide Widget")
        self.act_show_hide.triggered.connect(self.toggle_widget_visibility)
        
        self.act_settings = self.tray_menu.addAction("Settings")
        self.act_settings.triggered.connect(self.show_settings)
        
        self.act_refresh = self.tray_menu.addAction("Force Refresh")
        self.act_refresh.triggered.connect(self.force_refresh)
        
        self.tray_menu.addSeparator()
        self.act_exit = self.tray_menu.addAction("Exit")
        self.act_exit.triggered.connect(self.exit_app)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        # Connect widget events
        self.widget.open_settings_requested.connect(self.show_settings)
        self.widget.refresh_requested.connect(self.force_refresh)
        self.widget.exit_requested.connect(self.exit_app)

        # Poller thread
        self.poller = None
        # Shared HTTP client: reused across pollers so we don't re-login
        # (and trip LibreLinkUp's login rate-limit / get HTTP 429) on every
        # settings save or force refresh.
        self.client = LibreLinkUpClient()
        self.start_poller()

    def start_poller(self):
        if self.poller:
            self.poller.stop()
        self.poller = PollerThread(self.config_manager, self.client)
        self.poller.data_received.connect(self.on_data_received)
        self.poller.status_msg.connect(self.on_status_msg)
        self.poller.start()

    def update_tray_icon(self, val):
        """Draws a custom tray icon on the fly based on glucose value."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Choose color based on threshold
        high_t = self.config_manager.get("high_threshold")
        low_t = self.config_manager.get("low_threshold")
        
        if val >= high_t:
            bg_color = QColor("#ff9500") # Orange
        elif val <= low_t:
            bg_color = QColor("#ff3b30") # Red
        else:
            bg_color = QColor("#34c759") # Green

        # Draw circle
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        
        # Draw text value
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Outfit", 20, QFont.Bold))
        
        # Display unit conversion if mmol/L (e.g. 6.5)
        if self.config_manager.get("unit") == "mmol/L":
            display_val = val / 18.0182
            text = f"{display_val:.1f}"
            painter.setFont(QFont("Outfit", 18, QFont.Bold))
        else:
            text = str(int(val))
            
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))

    def on_data_received(self, val, arrow, timestamp, is_mock):
        self.widget.update_data(val, arrow, timestamp, is_mock)
        self.update_tray_icon(val)
        self.check_limits_and_notify(val)

    def on_status_msg(self, msg):
        self.widget.status_label.setText(msg)

    def check_limits_and_notify(self, val):
        if not self.config_manager.get("notifications_enabled"):
            return
            
        high_t = self.config_manager.get("high_threshold")
        low_t = self.config_manager.get("low_threshold")
        unit = self.config_manager.get("unit")
        
        # Formatting values for notification display
        if unit == "mmol/L":
            disp_val = val / 18.0182
            disp_high = high_t / 18.0182
            disp_low = low_t / 18.0182
            val_str = f"{disp_val:.1f} mmol/L"
            high_str = f"{disp_high:.1f} mmol/L"
            low_str = f"{disp_low:.1f} mmol/L"
        else:
            val_str = f"{int(val)} mg/dL"
            high_str = f"{int(high_t)} mg/dL"
            low_str = f"{int(low_t)} mg/dL"

        # Snooze and notification trigger logic
        if val >= high_t:
            if not self.config_manager.get("snoozed_high"):
                # Trigger notification
                self.tray_icon.showMessage(
                    "High Glucose Alert!",
                    f"Glucose level is {val_str}, which exceeds your high limit of {high_str}.",
                    QSystemTrayIcon.Warning,
                    8000
                )
                # Set snoozed flag to True so it doesn't alarm again until resetting
                self.config_manager.set("snoozed_high", True)
        elif val <= low_t:
            if not self.config_manager.get("snoozed_low"):
                # Trigger notification
                self.tray_icon.showMessage(
                    "Low Glucose Alert!",
                    f"Glucose level is {val_str}, which is below your low limit of {low_str}.",
                    QSystemTrayIcon.Critical,
                    8000
                )
                # Set snoozed flag to True
                self.config_manager.set("snoozed_low", True)
        else:
            # We are in the normal range, reset snoozes
            if self.config_manager.get("snoozed_high") or self.config_manager.get("snoozed_low"):
                self.config_manager.set("snoozed_high", False)
                self.config_manager.set("snoozed_low", False)

    def toggle_widget_visibility(self):
        if self.widget.isVisible():
            self.widget.hide()
            self.act_show_hide.setText("Show Widget")
        else:
            self.widget.show()
            self.widget.raise_()
            self.widget.activateWindow()
            self.act_show_hide.setText("Hide Widget")

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_widget_visibility()

    def show_settings(self):
        if self.settings_dlg is None:
            self.settings_dlg = SettingsDialog(self.config_manager)
            self.settings_dlg.settings_saved.connect(self.on_settings_saved)
            self.settings_dlg.finished.connect(self.on_settings_closed)
            self.settings_dlg.show()
            self.settings_dlg.raise_()
            self.settings_dlg.activateWindow()

    def on_settings_closed(self):
        self.settings_dlg = None

    def on_settings_saved(self):
        # Reload startup option
        startup_enabled = self.config_manager.get("startup_enabled")
        set_startup_registry(startup_enabled)
        
        # Apply updated settings to widget layout/styles
        self.widget.apply_settings()
        # Credentials/server may have changed -> drop the cached auth so the
        # next poller re-authenticates with the new settings.
        self.client.token = None
        self.client.user_id = None
        self.client.account_id_hash = None
        self.client.connections = []
        # Restart the poller with new settings
        self.start_poller()

    def force_refresh(self):
        self.widget.status_label.setText("Refreshing...")
        self.start_poller()

    def exit_app(self):
        if self.poller:
            self.poller.stop()
        self.tray_icon.hide()
        QApplication.quit()


def main():
    # Set high DPI scaling properties for modern screens
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    controller = AppController()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
