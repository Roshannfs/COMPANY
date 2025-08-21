<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# import sys

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QMenuBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QMainWindow,
    QAction, QToolBar, QStatusBar, QMessageBox, QFileDialog, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
       
        layout = QFormLayout()
       
        \# Camera settings
        layout.addRow(QLabel("Camera Settings:"))
        layout.addRow("Exposure Time:", QSpinBox())
        layout.addRow("Gain:", QSpinBox())
        layout.addRow("Resolution:", QComboBox())
       
        \# Detection settings
        layout.addRow(QLabel("Detection Settings:"))
        layout.addRow("Threshold:", QSpinBox())
        layout.addRow("Min Area:", QSpinBox())
        layout.addRow("Auto Adjust:", QCheckBox())
       
        \# Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
       
        layout.addRow(button_layout)
        self.setLayout(layout)

class MachineVisionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.init_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.apply_dark_styles()

def init_ui(self):
        self.setWindowTitle("Machine Vision System - Professional")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 600)
       
        \# Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

\# Main Layout with stretch
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

\# Camera layout with responsive grid
        camera_widget = QWidget()
        camera_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera_grid = QGridLayout(camera_widget)
        self.camera_grid.setSpacing(10)

\# Store camera frames for responsive updates
        self.camera_frames = []

\# Camera 1 - top left
        self.cam1_frame = QFrame()
        self.cam1_frame.setStyleSheet("background-color: \#3a3a3a; border: 2px solid \#555; border-radius: 5px;")
        self.cam1_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam1_frame.setMinimumSize(250, 200)
        cam1_label = QLabel("Camera 1", self.cam1_frame)
        cam1_label.setAlignment(Qt.AlignCenter)
        cam1_label.setFont(QFont('Arial', 12, QFont.Bold))
        cam1_label.setStyleSheet("color: \#ffffff; background: transparent; border: none;")
        vbox1 = QVBoxLayout(self.cam1_frame)
        vbox1.addStretch(1)
        vbox1.addWidget(cam1_label)
        vbox1.addStretch(10)
        self.camera_frames.append(self.cam1_frame)

\# Camera 2 - bottom left
        self.cam2_frame = QFrame()
        self.cam2_frame.setStyleSheet("background-color: \#3a3a3a; border: 2px solid \#555; border-radius: 5px;")
        self.cam2_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam2_frame.setMinimumSize(250, 200)
        cam2_label = QLabel("Camera 2", self.cam2_frame)
        cam2_label.setAlignment(Qt.AlignCenter)
        cam2_label.setFont(QFont('Arial', 12, QFont.Bold))
        cam2_label.setStyleSheet("color: \#ffffff; background: transparent; border: none;")
        vbox2 = QVBoxLayout(self.cam2_frame)
        vbox2.addStretch(1)
        vbox2.addWidget(cam2_label)
        vbox2.addStretch(10)
        self.camera_frames.append(self.cam2_frame)

\# Camera 3 - right center
        self.cam3_frame = QFrame()
        self.cam3_frame.setStyleSheet("background-color: \#3a3a3a; border: 2px solid \#555; border-radius: 5px;")
        self.cam3_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam3_frame.setMinimumSize(250, 400)
        cam3_label = QLabel("Camera 3", self.cam3_frame)
        cam3_label.setAlignment(Qt.AlignCenter)
        cam3_label.setFont(QFont('Arial', 12, QFont.Bold))
        cam3_label.setStyleSheet("color: \#ffffff; background: transparent; border: none;")
        vbox3 = QVBoxLayout(self.cam3_frame)
        vbox3.addStretch(1)
        vbox3.addWidget(cam3_label)
        vbox3.addStretch(10)
        self.camera_frames.append(self.cam3_frame)

\# Place camera frames in grid with proper stretching
        self.camera_grid.addWidget(self.cam1_frame, 0, 0)
        self.camera_grid.addWidget(self.cam2_frame, 1, 0)
        self.camera_grid.addWidget(self.cam3_frame, 0, 1, 2, 1)
       
        \# Set column and row stretches for responsive behavior
        self.camera_grid.setColumnStretch(0, 1)
        self.camera_grid.setColumnStretch(1, 1)
        self.camera_grid.setRowStretch(0, 1)
        self.camera_grid.setRowStretch(1, 1)

\# Right Side Layout with responsive sizing
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_widget.setMinimumWidth(300)
        right_widget.setMaximumWidth(400)
        right_layout = QVBoxLayout(right_widget)

\# Control Panel
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.StyledPanel)
        control_panel.setStyleSheet("background-color: \#404040; border: 1px solid \#666; border-radius: 5px; padding: 10px;")
        control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        control_layout = QVBoxLayout(control_panel)

entry_label = QLabel("Enter Barcode / Product Code:")
        entry_label.setFont(QFont('Arial', 10, QFont.Bold))
        entry_label.setStyleSheet("color: \#ffffff; background: transparent; border: none;")
        control_layout.addWidget(entry_label)

self.entry_box = QTextEdit()
        self.entry_box.setMinimumHeight(50)
        self.entry_box.setMaximumHeight(80)
        self.entry_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.entry_box.setStyleSheet("""
            QTextEdit {
                background-color: \#2a2a2a;
                border: 2px solid \#555;
                border-radius: 3px;
                color: \#ffffff;
                padding: 5px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 2px solid \#0078d4;
            }
        """)
        control_layout.addWidget(self.entry_box)

\# Control Buttons with responsive layout
        button_layout1 = QHBoxLayout()
        button_layout1.setSpacing(5)
        self.check_btn = QPushButton("Check")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.reset_btn = QPushButton("Reset")
       
        buttons1 = [self.check_btn, self.start_btn, self.stop_btn, self.reset_btn]
        for btn in buttons1:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: \#0078d4;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: \#106ebe;
                }
                QPushButton:pressed {
                    background-color: \#005a9e;
                }
            """)
            button_layout1.addWidget(btn)
        control_layout.addLayout(button_layout1)

\# Additional Control Buttons
        button_layout2 = QHBoxLayout()
        button_layout2.setSpacing(5)
        self.capture_btn = QPushButton("Capture")
        self.save_btn = QPushButton("Save")
        self.load_btn = QPushButton("Load")
        self.export_btn = QPushButton("Export")
       
        buttons2 = [self.capture_btn, self.save_btn, self.load_btn, self.export_btn]
        for btn in buttons2:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: \#6c757d;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: \#5a6268;
                }
                QPushButton:pressed {
                    background-color: \#495057;
                }
            """)
            button_layout2.addWidget(btn)
        control_layout.addLayout(button_layout2)

right_layout.addWidget(control_panel)

\# Validation Result with responsive sizing
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_box.setText(
            "Validation Result\n"
            "Camera 1: OK\n"
            "Camera 2: OK\n"
            "Camera 3: FAIL\n"
            "✗ Validation Failed!"
        )
        self.result_box.setStyleSheet("""
            QTextEdit {
                background-color: \#2a2a2a;
                border: 2px solid \#555;
                border-radius: 3px;
                color: \#ffffff;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        right_layout.addWidget(self.result_box)

\# Status Indicators with responsive sizing
        indicator_widget = QWidget()
        indicator_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setSpacing(15)
       
        fail_label = QLabel("FAIL:")
        fail_label.setStyleSheet("color: \#ffffff; font-weight: bold; font-size: 14px;")
        self.red_box = QFrame()
        self.red_box.setStyleSheet("background-color: \#dc3545; border: 2px solid \#c82333; border-radius: 5px;")
        self.red_box.setMinimumSize(50, 50)
        self.red_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
       
        pass_label = QLabel("PASS:")
        pass_label.setStyleSheet("color: \#ffffff; font-weight: bold; font-size: 14px;")
        self.green_box = QFrame()
        self.green_box.setStyleSheet("background-color: \#495057; border: 2px solid \#343a40; border-radius: 5px;")
        self.green_box.setMinimumSize(50, 50)
        self.green_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

indicator_layout.addWidget(fail_label)
        indicator_layout.addWidget(self.red_box)
        indicator_layout.addStretch()
        indicator_layout.addWidget(pass_label)
        indicator_layout.addWidget(self.green_box)

right_layout.addWidget(indicator_widget)

\# Add to main layout with proper stretching
        main_layout.addWidget(camera_widget, 3)  \# Camera area takes more space
        main_layout.addWidget(right_widget, 1)   \# Control panel takes less space

\# Connect button signals
        self.setup_connections()

def resizeEvent(self, event):
        """Handle window resize events for responsive behavior"""
        super().resizeEvent(event)
        self.update_camera_sizes()

def update_camera_sizes(self):
        """Update camera frame sizes based on available space"""
        if hasattr(self, 'camera_frames'):
            \# Get available space
            available_width = self.width() - 400  \# Reserve space for right panel
            available_height = self.height() - 150  \# Reserve space for menu/toolbar/status
           
            if self.is_fullscreen:
                \# In fullscreen, make cameras larger
                cam_width = max(400, available_width // 3)
                cam_height_single = max(300, available_height // 2)
                cam_height_full = max(600, available_height)
               
                \# Update indicator sizes for fullscreen
                self.red_box.setFixedSize(80, 80)
                self.green_box.setFixedSize(80, 80)
            else:
                \# Normal window sizing
                cam_width = max(250, available_width // 3)
                cam_height_single = max(200, available_height // 2)
                cam_height_full = max(400, available_height)
               
                \# Normal indicator sizes
                self.red_box.setFixedSize(60, 60)
                self.green_box.setFixedSize(60, 60)

\# Set minimum sizes for camera frames
            self.cam1_frame.setMinimumSize(cam_width, cam_height_single)
            self.cam2_frame.setMinimumSize(cam_width, cam_height_single)
            self.cam3_frame.setMinimumSize(cam_width, cam_height_full)

def apply_dark_styles(self):
        \# Apply dark stylesheet to the main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: \#2d2d2d;
                color: \#ffffff;
            }
            QMenuBar {
                background-color: \#3c3c3c;
                color: \#ffffff;
                border-bottom: 1px solid \#555;
                font-size: 12px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: \#0078d4;
            }
            QMenu {
                background-color: \#3c3c3c;
                color: \#ffffff;
                border: 1px solid \#555;
                font-size: 12px;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: \#0078d4;
            }
            QToolBar {
                background-color: \#3c3c3c;
                border: none;
                spacing: 2px;
                font-size: 12px;
            }
            QToolBar::separator {
                background-color: \#555;
                width: 1px;
                margin: 5px;
            }
            QStatusBar {
                background-color: \#3c3c3c;
                color: \#ffffff;
                border-top: 1px solid \#555;
                font-size: 12px;
            }
        """)

def setup_menu(self):
        menubar = self.menuBar()

\# File Menu
        file_menu = menubar.addMenu('File')
       
        new_action = QAction('New Project', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
       
        open_action = QAction('Open Project', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
       
        save_action = QAction('Save Project', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
       
        file_menu.addSeparator()
       
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

\# Camera Menu
        camera_menu = menubar.addMenu('Camera')
       
        connect_cameras = QAction('Connect All Cameras', self)
        connect_cameras.triggered.connect(self.connect_cameras)
        camera_menu.addAction(connect_cameras)
       
        disconnect_cameras = QAction('Disconnect All Cameras', self)
        disconnect_cameras.triggered.connect(self.disconnect_cameras)
        camera_menu.addAction(disconnect_cameras)
       
        camera_menu.addSeparator()
       
        calibrate_action = QAction('Calibrate Cameras', self)
        calibrate_action.triggered.connect(self.calibrate_cameras)
        camera_menu.addAction(calibrate_action)

\# Tools Menu
        tools_menu = menubar.addMenu('Tools')
       
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
       
        database_action = QAction('Database Management', self)
        database_action.triggered.connect(self.open_database)
        tools_menu.addAction(database_action)
       
        reports_action = QAction('Generate Reports', self)
        reports_action.triggered.connect(self.generate_reports)
        tools_menu.addAction(reports_action)

\# View Menu
        view_menu = menubar.addMenu('View')
       
        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
       
        zoom_in = QAction('Zoom In', self)
        zoom_in.setShortcut('Ctrl++')
        view_menu.addAction(zoom_in)
       
        zoom_out = QAction('Zoom Out', self)
        zoom_out.setShortcut('Ctrl+-')
        view_menu.addAction(zoom_out)

\# Help Menu
        help_menu = menubar.addMenu('Help')
       
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
       
        help_action = QAction('User Manual', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

def setup_toolbar(self):
        toolbar = self.addToolBar('Main')
        toolbar.setMovable(False)
       
        \# Quick access buttons
        start_action = QAction('Start', self)
        start_action.triggered.connect(self.start_inspection)
        toolbar.addAction(start_action)
       
        stop_action = QAction('Stop', self)
        stop_action.triggered.connect(self.stop_inspection)
        toolbar.addAction(stop_action)
       
        toolbar.addSeparator()
       
        capture_action = QAction('Capture', self)
        capture_action.triggered.connect(self.capture_image)
        toolbar.addAction(capture_action)
       
        toolbar.addSeparator()
       
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

def setup_statusbar(self):
        self.statusBar().showMessage('Ready - System Initialized')

def setup_connections(self):
        self.check_btn.clicked.connect(self.check_product)
        self.start_btn.clicked.connect(self.start_inspection)
        self.stop_btn.clicked.connect(self.stop_inspection)
        self.reset_btn.clicked.connect(self.reset_system)
        self.capture_btn.clicked.connect(self.capture_image)
        self.save_btn.clicked.connect(self.save_data)
        self.load_btn.clicked.connect(self.load_data)
        self.export_btn.clicked.connect(self.export_data)

\# Menu Actions
    def new_project(self):
        QMessageBox.information(self, "New Project", "Creating new project...")

def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.json)")
        if file_path:
            self.statusBar().showMessage(f"Opened: {file_path}")

def save_project(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.json)")
        if file_path:
            self.statusBar().showMessage(f"Saved: {file_path}")

def connect_cameras(self):
        self.statusBar().showMessage("Connecting cameras...")
        QMessageBox.information(self, "Camera", "All cameras connected successfully!")

def disconnect_cameras(self):
        self.statusBar().showMessage("Disconnecting cameras...")
        QMessageBox.information(self, "Camera", "All cameras disconnected!")

def calibrate_cameras(self):
        QMessageBox.information(self, "Calibration", "Camera calibration started...")

def open_settings(self):
        dialog = SettingsDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("Settings updated")

def open_database(self):
        QMessageBox.information(self, "Database", "Opening database management...")

def generate_reports(self):
        QMessageBox.information(self, "Reports", "Generating inspection reports...")

def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True
       
        \# Update sizes after fullscreen toggle
        QTimer.singleShot(100, self.update_camera_sizes)

def show_about(self):
        QMessageBox.about(self, "About",
                         "Machine Vision System v1.0\n\n"
                         "Professional quality inspection software\n"
                         "© 2025 Your Company")

def show_help(self):
        QMessageBox.information(self, "Help", "User manual will open in external browser...")

\# Button Actions
    def check_product(self):
        barcode = self.entry_box.toPlainText()
        self.statusBar().showMessage(f"Checking product: {barcode}")
       
    def start_inspection(self):
        self.statusBar().showMessage("Inspection started...")
       
    def stop_inspection(self):
        self.statusBar().showMessage("Inspection stopped")
       
    def reset_system(self):
        self.entry_box.clear()
        self.result_box.clear()
        self.statusBar().showMessage("System reset")
       
    def capture_image(self):
        self.statusBar().showMessage("Image captured from all cameras")
       
    def save_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv)")
        if file_path:
            self.statusBar().showMessage(f"Data saved to: {file_path}")
           
    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Data", "", "CSV Files (*.csv)")
        if file_path:
            self.statusBar().showMessage(f"Data loaded from: {file_path}")
           
    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", "PDF Files (*.pdf)")
        if file_path:
            self.statusBar().showMessage(f"Report exported to: {file_path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
   
    \# Apply dark theme palette
    dark_palette = QPalette()
    dark_color = QColor(45, 45, 45)
    disabled_color = QColor(127, 127, 127)
    text_color = QColor(220, 220, 220)

dark_palette.setColor(QPalette.Window, dark_color)
    dark_palette.setColor(QPalette.WindowText, text_color)
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QPalette.ToolTipBase, text_color)
    dark_palette.setColor(QPalette.ToolTipText, text_color)
    dark_palette.setColor(QPalette.Text, text_color)
    dark_palette.setColor(QPalette.Button, dark_color)
    dark_palette.setColor(QPalette.ButtonText, text_color)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)

app.setPalette(dark_palette)
   
    gui = MachineVisionGUI()
    gui.show()
    sys.exit(app.exec_()) and this code "import cv2
import easyocr
import pandas as pd
from datetime import datetime
import time
import os

# Settings

interval = 5  \# seconds between captures

# Get today's date for filename

today_str = datetime.now().strftime("%d-%m-%Y")
excel_file = f"product_info_{today_str}.xlsx"

# OCR Reader

reader = easyocr.Reader(['en'], gpu=False)  \# set gpu=True if you have CUDA

# Initialize camera

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open camera")

# Create Excel if not exists, else load and continue count

if os.path.exists(excel_file):
    df = pd.read_excel(excel_file)
    if not df.empty and "no of product" in df.columns:
        count = int(df["no of product"].max()) + 1
    else:
        df = pd.DataFrame(columns=["no of product", "time", "info"])
        df.to_excel(excel_file, index=False)
        count = 1
else:
    df = pd.DataFrame(columns=["no of product", "time", "info"])
    df.to_excel(excel_file, index=False)
    count = 1

last_capture_time = 0

print(f"Saving to file: {excel_file}")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

current_time = time.time()

\# Process every N seconds
    if current_time - last_capture_time >= interval:
        last_capture_time = current_time

\# Run OCR
        results = reader.readtext(frame)

\# If no text detected, keep empty
        if not results:
            text_detected = ""
        else:
            \# Join detected texts into one string
            text_detected = " | ".join([text for (_, text, conf) in results])

\# Current time in HH:MM:SS
        now_time = datetime.now().strftime("%H:%M:%S")

\# Append row
        new_row = {"no of product": count, "time": now_time, "info": text_detected}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

\# Save to Excel
        df.to_excel(excel_file, index=False)

print(f"[{now_time}] Capture \#{count} saved → {text_detected}")
        count += 1

\# Show camera feed
    cv2.imshow("Live Camera OCR", frame)

if cv2.waitKey(1) \& 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()" merge these two program

I'll merge these two programs to create a comprehensive machine vision system that combines the professional PyQt5 GUI with real-time OCR functionality. Here's the integrated solution:

