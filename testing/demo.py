import sys
import cv2
import numpy as np
import easyocr
import pandas as pd
from datetime import datetime
import time
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFrame, QMainWindow, QAction, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QSpinBox, QCheckBox, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QImage
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread

# ============ Global Settings ============
CAPTURE_INTERVAL = 5  # seconds between OCR captures
today_str = datetime.now().strftime("%d-%m-%Y")
excel_file = f"product_info_{today_str}.xlsx"

# Create Excel if not exists
if os.path.exists(excel_file):
    df = pd.read_excel(excel_file)
    if not df.empty and "no of product" in df.columns:
        PRODUCT_COUNT = int(df["no of product"].max()) + 1
    else:
        df = pd.DataFrame(columns=["no of product", "time", "camera", "info"])
        df.to_excel(excel_file, index=False)
        PRODUCT_COUNT = 1
else:
    df = pd.DataFrame(columns=["no of product", "time", "camera", "info"])
    df.to_excel(excel_file, index=False)
    PRODUCT_COUNT = 1

# OCR Reader
ocr_reader = easyocr.Reader(['en'], gpu=False)


# ============ Camera Worker Thread ============
class CameraThread(QThread):
    frameCaptured = pyqtSignal(int, np.ndarray, str)

    def __init__(self, cam_index, parent=None):
        super().__init__(parent)
        self.cam_index = cam_index
        self.running = True
        self.last_capture_time = 0

    def run(self):
        global PRODUCT_COUNT, df
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            print(f"❌ Camera {self.cam_index} cannot be opened")
            return

        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_time = time.time()
            if current_time - self.last_capture_time >= CAPTURE_INTERVAL:
                self.last_capture_time = current_time

                # Run OCR
                results = ocr_reader.readtext(frame)
                if results:
                    text_detected = " | ".join([text for (_, text, conf) in results])
                else:
                    text_detected = ""

                now_time = datetime.now().strftime("%H:%M:%S")

                # Append row to Excel
                new_row = {"no of product": PRODUCT_COUNT, "time": now_time,
                           "camera": f"Camera {self.cam_index+1}", "info": text_detected}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_excel(excel_file, index=False)

                print(f"[{now_time}] Cam {self.cam_index+1} Capture #{PRODUCT_COUNT} → {text_detected}")
                PRODUCT_COUNT += 1

                # Emit signal to GUI
                self.frameCaptured.emit(self.cam_index, frame, text_detected)
            else:
                self.frameCaptured.emit(self.cam_index, frame, "")

            time.sleep(0.03)

        cap.release()

    def stop(self):
        self.running = False
        self.wait()


# ============ Settings Dialog ============
class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
        layout = QFormLayout()
        layout.addRow("Capture Interval (s):", QSpinBox())
        layout.addRow("Auto Adjust:", QCheckBox())
        self.setLayout(layout)


# ============ Main GUI ============
class MachineVisionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.camera_threads = []
        self.captured_frames = [None, None, None]
        self.init_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.apply_dark_styles()
        self.setup_camera_threads()

    def init_ui(self):
        self.setWindowTitle("Machine Vision System")
        self.setGeometry(100, 100, 1200, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Camera grid
        camera_widget = QWidget()
        self.camera_grid = QGridLayout(camera_widget)
        self.cam_labels = []

        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555;")
            vbox = QVBoxLayout(frame)
            label = QLabel(f"Camera {i+1}")
            label.setStyleSheet("color: white;")
            img = QLabel()
            img.setAlignment(Qt.AlignCenter)
            img.setScaledContents(True)
            vbox.addWidget(label)
            vbox.addWidget(img)
            self.cam_labels.append(img)
            if i < 2:
                self.camera_grid.addWidget(frame, i, 0)
            else:
                self.camera_grid.addWidget(frame, 0, 1, 2, 1)

        # Right panel
        right_panel = QVBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.export_btn = QPushButton("Export")
        for btn in [self.start_btn, self.stop_btn, self.export_btn]:
            right_panel.addWidget(btn)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        right_panel.addWidget(self.result_box)

        main_layout.addWidget(camera_widget, 4)
        main_layout.addLayout(right_panel, 1)

        # Button connections
        self.start_btn.clicked.connect(self.start_inspection)
        self.stop_btn.clicked.connect(self.stop_inspection)
        self.export_btn.clicked.connect(self.export_data)

    def setup_camera_threads(self):
        for idx in [0, 1, 2]:   # replace with actual indexes available in your system
            thread = CameraThread(idx)
            thread.frameCaptured.connect(self.update_camera_view)
            thread.start()
            self.camera_threads.append(thread)

    def update_camera_view(self, cam_index, frame, text_detected):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_labels[cam_index].setPixmap(QPixmap.fromImage(qt_img))

        if text_detected:
            self.result_box.append(f"Cam {cam_index+1}: {text_detected}")

    def start_inspection(self):
        self.statusBar().showMessage("Inspection started...")

    def stop_inspection(self):
        self.statusBar().showMessage("Inspection stopped")
        for thread in self.camera_threads:
            thread.stop()

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", "Excel Files (*.xlsx)")
        if file_path:
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Export", f"Data exported to {file_path}")

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def setup_statusbar(self):
        self.statusBar().showMessage('Ready - System Initialized')

    def apply_dark_styles(self):
        self.setStyleSheet("QMainWindow { background-color: #2d2d2d; color: #ffffff; }")

    def closeEvent(self, event):
        for thread in self.camera_threads:
            thread.stop()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    palette = QPalette()
    dark_color = QColor(45, 45, 45)
    text_color = QColor(220, 220, 220)
    palette.setColor(QPalette.Window, dark_color)
    palette.setColor(QPalette.WindowText, text_color)
    app.setPalette(palette)

    gui = MachineVisionGUI()
    gui.show()
    sys.exit(app.exec_())
