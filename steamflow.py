import sys
import os
import psutil
import winreg
import yaml
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTabWidget,
                             QCheckBox, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

class SteamOptimizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SteamFlow - Steam Optimizer")
        self.setMinimumSize(800, 600)
        self.setup_theme()
        self.setup_ui()

    def setup_theme(self):
        # Set up dark OLED theme with iris accents
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(10, 10, 10))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(88, 170, 255))  # Iris accent
        palette.setColor(QPalette.ColorRole.Link, QColor(88, 170, 255))  # Iris accent
        palette.setColor(QPalette.ColorRole.Highlight, QColor(88, 170, 255))  # Iris accent
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

        self.setPalette(palette)
        app = QApplication.instance()
        app.setPalette(palette)

        # Set Consolas font
        app_font = QFont("Consolas", 10)
        app.setFont(app_font)

    def calculate_cache_size(self):
        try:
            steam_path = self._get_steam_path()
            if not steam_path:
                self.cache_size.setText("Cache Size: Steam installation not found")
                return

            cache_paths = {
                "App Cache": os.path.join(steam_path, "appcache"),
                "Depot Cache": os.path.join(steam_path, "depotcache"),
                "Download Cache": os.path.join(steam_path, "download")
            }

            total_size = 0
            cache_details = []

            for cache_name, path in cache_paths.items():
                size = 0
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        size += sum(os.path.getsize(os.path.join(root, file)) 
                                   for file in files if os.path.exists(os.path.join(root, file)))
                size_mb = size / 1024 / 1024
                total_size += size_mb
                cache_details.append(f"{cache_name}: {size_mb:.1f} MB")

            cache_text = f"Total Cache Size: {total_size:.1f} MB\n" + "\n".join(cache_details)
            self.cache_size.setText(cache_text)

        except Exception as e:
            self.cache_size.setText(f"Error calculating cache size: {str(e)}")

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create tab widget with custom styling
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #404040; }
            QTabWidget::tab-bar { left: 5px; }
            QTabBar::tab { 
                background: #202020; 
                color: white;
                padding: 8px 12px;
                margin-right: 2px;
                border: 1px solid #404040;
                border-bottom: none;
            }
            QTabBar::tab:selected { 
                background: #58AAFF;
                color: black;
            }
        """)
        layout.addWidget(tabs)

        # Process Optimization Tab
        process_tab = QWidget()
        process_layout = QVBoxLayout(process_tab)

        # Process list and controls
        self.process_list = QLabel("Steam Processes:")
        process_layout.addWidget(self.process_list)
        self.update_process_list()

        # Process optimization buttons
        optimize_btn = QPushButton("Optimize Processes")
        optimize_btn.clicked.connect(self.optimize_processes)
        process_layout.addWidget(optimize_btn)

        tabs.addTab(process_tab, "Process Optimization")

        # Telemetry Control Tab
        telemetry_tab = QWidget()
        telemetry_layout = QVBoxLayout(telemetry_tab)

        # Telemetry blocking options
        self.block_updates = QCheckBox("Block Automatic Updates")
        self.block_metrics = QCheckBox("Block Usage Metrics")
        self.block_browser = QCheckBox("Block Built-in Browser")

        telemetry_layout.addWidget(self.block_updates)
        telemetry_layout.addWidget(self.block_metrics)
        telemetry_layout.addWidget(self.block_browser)

        # Apply telemetry settings button
        apply_btn = QPushButton("Apply Telemetry Settings")
        apply_btn.clicked.connect(self.apply_telemetry_settings)
        telemetry_layout.addWidget(apply_btn)

        tabs.addTab(telemetry_tab, "Telemetry Control")

        # Cache Management Tab with enhanced UI
        cache_tab = QWidget()
        cache_layout = QVBoxLayout(cache_tab)

        # Cache info with detailed breakdown
        self.cache_size = QLabel("Cache Size: Calculating...")
        self.cache_size.setWordWrap(True)
        self.cache_size.setStyleSheet("padding: 10px; background: #101010; border-radius: 5px;")
        cache_layout.addWidget(self.cache_size)

        # Update cache size initially and set up timer for updates
        self.calculate_cache_size()
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self.calculate_cache_size)
        self.cache_timer.start(10000)  # Update every 10 seconds

        clear_cache_btn = QPushButton("Clear Steam Cache")
        clear_cache_btn.setStyleSheet("""
            QPushButton { 
                background: #58AAFF; 
                color: black; 
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7AB8FF; }
            QPushButton:pressed { background: #3890FF; }
        """)
        clear_cache_btn.clicked.connect(self.clear_cache)
        cache_layout.addWidget(clear_cache_btn)

        tabs.addTab(cache_tab, "Cache Management")

        # Status bar for feedback
        self.statusBar().showMessage("Ready")

        # Timer for updating process list
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_process_list)
        self.timer.start(5000)  # Update every 5 seconds

    def update_process_list(self):
        steam_processes = []
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                if 'steam' in proc.info['name'].lower():
                    mem = proc.info['memory_info'].rss / 1024 / 1024  # Convert to MB
                    steam_processes.append(f"{proc.info['name']}: {mem:.1f} MB")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        process_text = "Steam Processes:\n" + "\n".join(steam_processes)
        self.process_list.setText(process_text)

    def optimize_processes(self):
        optimized = 0
        for proc in psutil.process_iter(['name']):
            try:
                if 'steam' in proc.info['name'].lower():
                    if 'steamwebhelper' in proc.info['name'].lower():
                        proc.terminate()
                        optimized += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        QMessageBox.information(self, "Process Optimization",
                              f"Optimized {optimized} unnecessary processes")

    def apply_telemetry_settings(self):
        try:
            steam_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\\Valve\\Steam")

            if self.block_updates.isChecked():
                winreg.SetValueEx(steam_key, "AutoUpdateWindowEnabled", 0,
                                winreg.REG_DWORD, 0)

            if self.block_metrics.isChecked():
                winreg.SetValueEx(steam_key, "Metrics", 0, winreg.REG_DWORD, 0)

            if self.block_browser.isChecked():
                winreg.SetValueEx(steam_key, "EnableGameOverlay", 0,
                                winreg.REG_DWORD, 0)

            QMessageBox.information(self, "Settings Applied",
                                  "Telemetry settings have been updated")

        except Exception as e:
            QMessageBox.warning(self, "Error",
                              f"Failed to apply settings: {str(e)}")

    def clear_cache(self):
        try:
            steam_path = self._get_steam_path()
            if not steam_path:
                raise Exception("Steam installation not found")

            cache_paths = [
                os.path.join(steam_path, "appcache"),
                os.path.join(steam_path, "depotcache"),
                os.path.join(steam_path, "download")
            ]

            cleared_size = 0
            for path in cache_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleared_size += size
                            except:
                                pass

            cleared_mb = cleared_size / 1024 / 1024
            QMessageBox.information(self, "Cache Cleared",
                                  f"Cleared {cleared_mb:.1f} MB of cache")

        except Exception as e:
            QMessageBox.warning(self, "Error",
                              f"Failed to clear cache: {str(e)}")

    def _get_steam_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\\WOW6432Node\\Valve\\Steam")
            return winreg.QueryValueEx(key, "InstallPath")[0]
        except:
            return None

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    window = SteamOptimizer()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()