import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QMenuBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QMainWindow,
    QAction, QToolBar, QStatusBar, QMessageBox, QFileDialog, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
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

class CameraPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_frames = []
        self.camera_grid = QGridLayout(self)
        self.camera_grid.setSpacing(10)
        self.init_cameras()

    def init_cameras(self):
        self.cam1_frame = self.create_camera_frame("Camera 1")
        self.cam2_frame = self.create_camera_frame("Camera 2")
        self.cam3_frame = self.create_camera_frame("Camera 3", min_height=400)
        self.camera_grid.addWidget(self.cam1_frame, 0, 0)
        self.camera_grid.addWidget(self.cam2_frame, 1, 0)
        self.camera_grid.addWidget(self.cam3_frame, 0, 1, 2, 1)
        self.camera_grid.setColumnStretch(0, 1)
        self.camera_grid.setColumnStretch(1, 1)
        self.camera_grid.setRowStretch(0, 1)
        self.camera_grid.setRowStretch(1, 1)
        self.camera_frames = [self.cam1_frame, self.cam2_frame, self.cam3_frame]

    def create_camera_frame(self, label_text, min_height=200):
        frame = QFrame()
        frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555; border-radius: 5px;")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setMinimumSize(250, min_height)
        label = QLabel(label_text, frame)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont('Arial', 12, QFont.Bold))
        label.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        vbox = QVBoxLayout(frame)
        vbox.addStretch(1)
        vbox.addWidget(label)
        vbox.addStretch(10)
        return frame

class ControlPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #404040; border: 1px solid #666; border-radius: 5px; padding: 10px;")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        entry_label = QLabel("Enter Barcode / Product Code:")
        entry_label.setFont(QFont('Arial', 10, QFont.Bold))
        entry_label.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        self.layout.addWidget(entry_label)
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
        self.layout.addWidget(self.entry_box)
        self.init_buttons()

    def init_buttons(self):
        self.check_btn = QPushButton("Check")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.reset_btn = QPushButton("Reset")
        self.capture_btn = QPushButton("Capture")
        self.save_btn = QPushButton("Save")
        self.load_btn = QPushButton("Load")
        self.export_btn = QPushButton("Export")
        button_layout1 = QHBoxLayout()
        for btn in [self.check_btn, self.start_btn, self.stop_btn, self.reset_btn]:
            self.style_button(btn, "#0078d4", "#106ebe", "#005a9e")
            button_layout1.addWidget(btn)
        self.layout.addLayout(button_layout1)
        button_layout2 = QHBoxLayout()
        for btn in [self.capture_btn, self.save_btn, self.load_btn, self.export_btn]:
            self.style_button(btn, "#6c757d", "#5a6268", "#495057")
            button_layout2.addWidget(btn)
        self.layout.addLayout(button_layout2)

    def style_button(self, btn, color, hover, pressed):
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumHeight(35)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """)

class StatusIndicators(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
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
        layout.addWidget(fail_label)
        layout.addWidget(self.red_box)
        layout.addStretch()
        layout.addWidget(pass_label)
        layout.addWidget(self.green_box)

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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        # Camera panel
        self.camera_panel = CameraPanel()
        # Right panel
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_widget.setMinimumWidth(300)
        right_widget.setMaximumWidth(400)
        right_layout = QVBoxLayout(right_widget)
        # Control panel
        self.control_panel = ControlPanel()
        right_layout.addWidget(self.control_panel)
        # Result box
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
        # Status indicators
        self.status_indicators = StatusIndicators()
        right_layout.addWidget(self.status_indicators)
        # Add to main layout
        main_layout.addWidget(self.camera_panel, 3)
        main_layout.addWidget(right_widget, 1)
        self.setup_connections()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_camera_sizes()

    def update_camera_sizes(self):
        available_width = self.width() - 400
        available_height = self.height() - 150
        if self.is_fullscreen:
            cam_width = max(400, available_width // 3)
            cam_height_single = max(300, available_height // 2)
            cam_height_full = max(600, available_height)
            self.status_indicators.red_box.setFixedSize(80, 80)
            self.status_indicators.green_box.setFixedSize(80, 80)
        else:
            cam_width = max(250, available_width // 3)
            cam_height_single = max(200, available_height // 2)
            cam_height_full = max(400, available_height)
            self.status_indicators.red_box.setFixedSize(60, 60)
            self.status_indicators.green_box.setFixedSize(60, 60)
        self.camera_panel.cam1_frame.setMinimumSize(cam_width, cam_height_single)
        self.camera_panel.cam2_frame.setMinimumSize(cam_width, cam_height_single)
        self.camera_panel.cam3_frame.setMinimumSize(cam_width, cam_height_full)

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
        file_menu.addAction(self.create_action('New Project', self.new_project, 'Ctrl+N'))
        file_menu.addAction(self.create_action('Open Project', self.open_project, 'Ctrl+O'))
        file_menu.addAction(self.create_action('Save Project', self.save_project, 'Ctrl+S'))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action('Exit', self.close, 'Ctrl+Q'))
        camera_menu = menubar.addMenu('Camera')
        camera_menu.addAction(self.create_action('Connect All Cameras', self.connect_cameras))
        camera_menu.addAction(self.create_action('Disconnect All Cameras', self.disconnect_cameras))
        camera_menu.addSeparator()
        camera_menu.addAction(self.create_action('Calibrate Cameras', self.calibrate_cameras))
        tools_menu = menubar.addMenu('Tools')
        tools_menu.addAction(self.create_action('Settings', self.open_settings))
        tools_menu.addAction(self.create_action('Database Management', self.open_database))
        tools_menu.addAction(self.create_action('Generate Reports', self.generate_reports))
        view_menu = menubar.addMenu('View')
        view_menu.addAction(self.create_action('Fullscreen', self.toggle_fullscreen, 'F11'))
        view_menu.addAction(self.create_action('Zoom In', lambda: None, 'Ctrl++'))
        view_menu.addAction(self.create_action('Zoom Out', lambda: None, 'Ctrl+-'))
        help_menu = menubar.addMenu('Help')
        help_menu.addAction(self.create_action('About', self.show_about))
        help_menu.addAction(self.create_action('User Manual', self.show_help, 'F1'))

    def create_action(self, text, slot, shortcut=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    def setup_toolbar(self):
        toolbar = self.addToolBar('Main')
        toolbar.setMovable(False)
        toolbar.addAction(self.create_action('Start', self.start_inspection))
        toolbar.addAction(self.create_action('Stop', self.stop_inspection))
        toolbar.addSeparator()
        toolbar.addAction(self.create_action('Capture', self.capture_image))
        toolbar.addSeparator()
        toolbar.addAction(self.create_action('Settings', self.open_settings))

    def setup_statusbar(self):
        self.statusBar().showMessage('Ready - System Initialized')

    def setup_connections(self):
        cp = self.control_panel
        cp.check_btn.clicked.connect(self.check_product)
        cp.start_btn.clicked.connect(self.start_inspection)
        cp.stop_btn.clicked.connect(self.stop_inspection)
        cp.reset_btn.clicked.connect(self.reset_system)
        cp.capture_btn.clicked.connect(self.capture_image)
        cp.save_btn.clicked.connect(self.save_data)
        cp.load_btn.clicked.connect(self.load_data)
        cp.export_btn.clicked.connect(self.export_data)

    # Menu Actions
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
        QTimer.singleShot(100, self.update_camera_sizes)

    def show_about(self):
        QMessageBox.about(self, "About", 
                         "Machine Vision System v1.0\n\n"
                         "Professional quality inspection software\n"
                         "© 2025 Your Company")

    def show_help(self):
        QMessageBox.information(self, "Help", "User manual will open in external browser...")

    # Button Actions
    def check_product(self):
        barcode = self.control_panel.entry_box.toPlainText()
        self.statusBar().showMessage(f"Checking product: {barcode}")

    def start_inspection(self):
        self.statusBar().showMessage("Inspection started...")

    def stop_inspection(self):
        self.statusBar().showMessage("Inspection stopped")

    def reset_system(self):
        self.control_panel.entry_box.clear()
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

def apply_dark_palette(app):
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

def main():
    app = QApplication(sys.argv)
    apply_dark_palette(app)
    gui = MachineVisionGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
