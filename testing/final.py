import sys
import cv2
import imutils
import numpy as np
import easyocr
import pandas as pd
from datetime import datetime
import time
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QMenuBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QMainWindow,
    QAction, QToolBar, QStatusBar, QMessageBox, QFileDialog, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QImage
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread

# =======================
# CONFIGURE CAMERA INDICES
# Put the OpenCV device IDs for Iriun 1, 2, 3 here.
# Example: [0, 1, 2]  or if your OS gives 3 cams as 3,5,6 then [3, 5, 6]
CAM_INDICES = [0, 1, 2]
# =======================

# --- Camera Worker Thread for Live Feed ---
class CameraThread(QThread):
    frameCaptured = pyqtSignal(int, np.ndarray)

    def __init__(self, cam_index, parent=None):
        super().__init__(parent)
        self.cam_index = cam_index
        self.running = True
        self.cap = None

    def run(self):
        self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)  # CAP_DSHOW helps on Windows
        if not self.cap.isOpened():
            # emit nothing; just exit the thread gracefully
            return
        # Optional: reduce latency
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frameCaptured.emit(self.cam_index, frame)
            time.sleep(0.03)  # ~30 FPS
        self.cap.release()

    def stop(self):
        self.running = False
        self.wait()


# --- Settings Dialog ---
class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
        layout = QFormLayout()
        layout.addRow(QLabel("Camera Settings:"))
        layout.addRow("Exposure Time:", QSpinBox())
        layout.addRow("Gain:", QSpinBox())
        layout.addRow("Resolution:", QComboBox())
        layout.addRow(QLabel("Detection Settings:"))
        layout.addRow("Threshold:", QSpinBox())
        layout.addRow("Min Area:", QSpinBox())
        layout.addRow("Auto Adjust:", QCheckBox())
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        self.setLayout(layout)


# --- Main GUI ---
class MachineVisionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False

        # Map camera index -> display slot (0,1,2)
        # e.g., if CAM_INDICES = [3,5,6], then cam_to_slot = {3:0, 5:1, 6:2}
        self.cam_to_slot = {cam_idx: slot for slot, cam_idx in enumerate(CAM_INDICES)}

        self.init_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.apply_dark_styles()

        self.camera_threads = []
        self.captured_frames = [None, None, None]  # slots 0,1,2

        self.ocr_reader = easyocr.Reader(['en'], gpu=False)

        self.setup_camera_threads()

    def init_ui(self):
        self.setWindowTitle("Machine Vision System - Professional")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Camera widget - now takes more space
        camera_widget = QWidget()
        camera_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera_grid = QGridLayout(camera_widget)
        self.camera_grid.setSpacing(10)
        self.camera_frames = []

        # Camera 1
        self.cam1_frame = QFrame()
        self.cam1_frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555; border-radius: 5px;")
        self.cam1_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam1_frame.setMinimumSize(300, 300)
        self.cam1_label = QLabel("Camera 1", self.cam1_frame)
        self.cam1_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.cam1_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.cam1_label.setStyleSheet("color: #ffffff; background: transparent; border: none; padding: 5px;")
        self.cam1_img = QLabel(self.cam1_frame)
        self.cam1_img.setAlignment(Qt.AlignCenter)
        self.cam1_img.setScaledContents(True)
        vbox1 = QVBoxLayout(self.cam1_frame)
        vbox1.setContentsMargins(5, 5, 5, 5)
        vbox1.addWidget(self.cam1_label, 0)
        vbox1.addWidget(self.cam1_img, 1)
        self.camera_frames.append(self.cam1_frame)

        # Camera 2
        self.cam2_frame = QFrame()
        self.cam2_frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555; border-radius: 5px;")
        self.cam2_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam2_frame.setMinimumSize(300, 300)
        self.cam2_label = QLabel("Camera 2", self.cam2_frame)
        self.cam2_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.cam2_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.cam2_label.setStyleSheet("color: #ffffff; background: transparent; border: none; padding: 5px;")
        self.cam2_img = QLabel(self.cam2_frame)
        self.cam2_img.setAlignment(Qt.AlignCenter)
        self.cam2_img.setScaledContents(True)
        vbox2 = QVBoxLayout(self.cam2_frame)
        vbox2.setContentsMargins(5, 5, 5, 5)
        vbox2.addWidget(self.cam2_label, 0)
        vbox2.addWidget(self.cam2_img, 1)
        self.camera_frames.append(self.cam2_frame)

        # Camera 3
        self.cam3_frame = QFrame()
        self.cam3_frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555; border-radius: 5px;")
        self.cam3_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam3_frame.setMinimumSize(300, 600)
        self.cam3_label = QLabel("Camera 3", self.cam3_frame)
        self.cam3_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.cam3_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.cam3_label.setStyleSheet("color: #ffffff; background: transparent; border: none; padding: 5px;")
        self.cam3_img = QLabel(self.cam3_frame)
        self.cam3_img.setAlignment(Qt.AlignCenter)
        self.cam3_img.setScaledContents(True)
        vbox3 = QVBoxLayout(self.cam3_frame)
        vbox3.setContentsMargins(5, 5, 5, 5)
        vbox3.addWidget(self.cam3_label, 0)
        vbox3.addWidget(self.cam3_img, 1)
        self.camera_frames.append(self.cam3_frame)

        # Place camera frames in grid
        self.camera_grid.addWidget(self.cam1_frame, 0, 0)
        self.camera_grid.addWidget(self.cam2_frame, 1, 0)
        self.camera_grid.addWidget(self.cam3_frame, 0, 1, 2, 1)
        self.camera_grid.setColumnStretch(0, 1)
        self.camera_grid.setColumnStretch(1, 1)
        self.camera_grid.setRowStretch(0, 1)
        self.camera_grid.setRowStretch(1, 1)

        # Right Side Layout
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_widget.setMinimumWidth(250)
        right_widget.setMaximumWidth(300)
        right_layout = QVBoxLayout(right_widget)

        # Control Panel
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.StyledPanel)
        control_panel.setStyleSheet("background-color: #404040; border: 1px solid #666; border-radius: 5px; padding: 10px;")
        control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        control_layout = QVBoxLayout(control_panel)

        entry_label = QLabel("Enter Barcode / Product Code:")
        entry_label.setFont(QFont('Arial', 10, QFont.Bold))
        entry_label.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        control_layout.addWidget(entry_label)

        self.entry_box = QTextEdit()
        self.entry_box.setMinimumHeight(50)
        self.entry_box.setMaximumHeight(80)
        self.entry_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.entry_box.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 3px;
                color: #ffffff;
                padding: 5px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        control_layout.addWidget(self.entry_box)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.export_btn = QPushButton("Export")

        buttons = [self.start_btn, self.stop_btn, self.export_btn]
        for btn in buttons:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
            button_layout.addWidget(btn)

        control_layout.addLayout(button_layout)
        right_layout.addWidget(control_panel)

        # Result display
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
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 3px;
                color: #ffffff;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        right_layout.addWidget(self.result_box)

        # Indicator lights
        indicator_widget = QWidget()
        indicator_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setSpacing(15)

        fail_label = QLabel("FAIL:")
        fail_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.red_box = QFrame()
        self.red_box.setStyleSheet("background-color: #dc3545; border: 2px solid #c82333; border-radius: 5px;")
        self.red_box.setMinimumSize(50, 50)
        self.red_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        pass_label = QLabel("PASS:")
        pass_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.green_box = QFrame()
        self.green_box.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")
        self.green_box.setMinimumSize(50, 50)
        self.green_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        indicator_layout.addWidget(fail_label)
        indicator_layout.addWidget(self.red_box)
        indicator_layout.addStretch()
        indicator_layout.addWidget(pass_label)
        indicator_layout.addWidget(self.green_box)

        right_layout.addWidget(indicator_widget)

        # Adjust main layout proportions
        main_layout.addWidget(camera_widget, 4)
        main_layout.addWidget(right_widget, 1)

        self.setup_connections()

    def setup_camera_threads(self):
        # Start threads for the 3 desired camera indices
        for idx in CAM_INDICES:
            thread = CameraThread(idx)
            thread.frameCaptured.connect(self.update_camera_view)
            thread.start()
            self.camera_threads.append(thread)

        self.statusBar().showMessage(f"Started camera threads for indices: {CAM_INDICES}")

    # Helper: get the correct QLabel for a given slot (0,1,2)
    def _label_for_slot(self, slot):
        if slot == 0:
            return self.cam1_img
        elif slot == 1:
            return self.cam2_img
        elif slot == 2:
            return self.cam3_img
        return None

    def update_camera_view(self, cam_index, frame):
        """
        Receives frames from threads. Maps physical camera index (e.g., 0/1/2 or 3/5/6)
        to display slot 0/1/2 and updates the right QLabel.
        """
        if cam_index not in self.cam_to_slot:
            return

        slot = self.cam_to_slot[cam_index]
        target_label = self._label_for_slot(slot)
        if target_label is None:
            return

        # Resize frame to fit the label while keeping aspect ratio
        h, w = frame.shape[:2]
        label_size = target_label.size()
        label_w, label_h = label_size.width(), label_size.height()

        if label_w > 0 and label_h > 0:
            scale = min(label_w / w, label_h / h)
            new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
            disp_frame = cv2.resize(frame, (new_w, new_h))
        else:
            disp_frame = imutils.resize(frame, width=400)

        rgb_image = cv2.cvtColor(disp_frame, cv2.COLOR_BGR2RGB)
        h2, w2, ch = rgb_image.shape
        bytes_per_line = ch * w2
        qt_img = QImage(rgb_image.data, w2, h2, bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qt_img)

        target_label.setPixmap(pixmap)
        self.captured_frames[slot] = frame

    def closeEvent(self, event):
        for thread in self.camera_threads:
            thread.stop()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_camera_sizes()

    def update_camera_sizes(self):
        if hasattr(self, 'camera_frames'):
            available_width = self.width() - 350  # Adjusted for right panel width
            available_height = self.height() - 150

            if self.is_fullscreen:
                cam_width = max(500, available_width // 2)
                cam_height_single = max(400, available_height // 2)
                cam_height_full = max(800, available_height)
                self.red_box.setFixedSize(80, 80)
                self.green_box.setFixedSize(80, 80)
            else:
                cam_width = max(300, available_width // 2)
                cam_height_single = max(300, available_height // 2)
                cam_height_full = max(600, available_height)
                self.red_box.setFixedSize(60, 60)
                self.green_box.setFixedSize(60, 60)

            self.cam1_frame.setMinimumSize(cam_width, cam_height_single)
            self.cam2_frame.setMinimumSize(cam_width, cam_height_single)
            self.cam3_frame.setMinimumSize(cam_width, cam_height_full)

    def apply_dark_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-bottom: 1px solid #555;
                font-size: 12px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                font-size: 12px;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                spacing: 2px;
                font-size: 12px;
            }
            QToolBar::separator {
                background-color: #555;
                width: 1px;
                margin: 5px;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555;
                font-size: 12px;
            }
        """)

    def setup_menu(self):
        menubar = self.menuBar()

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

        start_action = QAction('Start', self)
        start_action.triggered.connect(self.start_inspection)
        toolbar.addAction(start_action)

        stop_action = QAction('Stop', self)
        stop_action.triggered.connect(self.stop_inspection)
        toolbar.addAction(stop_action)

        toolbar.addSeparator()

        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

    def setup_statusbar(self):
        self.statusBar().showMessage('Ready - System Initialized')

    def setup_connections(self):
        self.start_btn.clicked.connect(self.start_inspection)
        self.stop_btn.clicked.connect(self.stop_inspection)
        self.export_btn.clicked.connect(self.export_data)

    # --- Menu Actions ---
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
        self.statusBar().showMessage("Cameras already started at launch.")

    def disconnect_cameras(self):
        self.statusBar().showMessage("Disconnecting cameras...")
        for t in self.camera_threads:
            t.stop()
        self.camera_threads.clear()
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
        QTimer.singleShot(100, self.update_camera_sizes)

    def show_about(self):
        QMessageBox.about(self, "About",
                          "Machine Vision System v1.0\n\n"
                          "Professional quality inspection software\n"
                          "© 2025 Your Company")

    def show_help(self):
        QMessageBox.information(self, "Help", "User manual will open in external browser...")

    # --- Button Actions ---
    def start_inspection(self):
        self.statusBar().showMessage("Inspection started...")

    def stop_inspection(self):
        self.statusBar().showMessage("Inspection stopped")

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", "PDF Files (*.pdf);;CSV Files (*.csv)")
        if file_path:
            self.statusBar().showMessage(f"Report exported to: {file_path}")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Dark theme palette
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

    sys.exit(app.exec_())
