import sys
import os
import cv2
import threading
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
import easyocr

# Database Manager Class
class DatabaseManager:
    def __init__(self, db_name="machine_vision.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT,
                timestamp DATETIME,
                camera_1_text TEXT,
                camera_2_text TEXT,
                camera_3_text TEXT,
                validation_result TEXT,
                image_path TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_product(self, product_code, cam1_text, cam2_text, cam3_text, validation, image_path):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (product_code, timestamp, camera_1_text, camera_2_text, camera_3_text, validation_result, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_code, datetime.now(), cam1_text, cam2_text, cam3_text, validation, image_path))
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id

    def search_product(self, product_code):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_code = ? ORDER BY timestamp DESC', (product_code,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_all_products(self):
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM products ORDER BY timestamp DESC", conn)
        conn.close()
        return df

# OCR Manager Class
class OCRManager:
    def __init__(self):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    def read_text(self, frame):
        if frame is None:
            return ""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.reader.readtext(rgb_frame)
            if not results:
                return ""
            return " | ".join([result[1] for result in results])
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

# Camera Manager Class
class CameraManager(QThread):
    frame_ready = pyqtSignal(int, object)  # camera_id, frame

    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.cap = None
        self.running = False
        self.connect_camera()

    def connect_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_id)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                print(f"Camera {self.camera_id} connected successfully")
                return True
        except Exception as e:
            print(f"Camera {self.camera_id} connection failed: {e}")
            return False

    def run(self):
        self.running = True
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(self.camera_id, frame)
            self.msleep(33)  # ~30 FPS

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()
        self.wait()

# Excel Manager Class
class ExcelManager:
    def __init__(self):
        self.create_excel_file()

    def create_excel_file(self):
        today_str = datetime.now().strftime("%d-%m-%Y_%H%M%S")
        self.filename = f"product_info_{today_str}.xlsx"
        df = pd.DataFrame(columns=[
            "ID", "Product Code", "Timestamp", "Camera 1 Text", 
            "Camera 2 Text", "Camera 3 Text", "Validation Result"
        ])
        df.to_excel(self.filename, index=False)

    def append_data(self, product_id, product_code, cam1_text, cam2_text, cam3_text, validation):
        try:
            df = pd.read_excel(self.filename)
            new_row = {
                "ID": product_id,
                "Product Code": product_code,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Camera 1 Text": cam1_text,
                "Camera 2 Text": cam2_text,
                "Camera 3 Text": cam3_text,
                "Validation Result": validation
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel(self.filename, index=False)
        except Exception as e:
            print(f"Excel write error: {e}")

# Database View Dialog
class DatabaseViewDialog(QDialog):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database View")
        self.setGeometry(200, 200, 1000, 600)

        layout = QVBoxLayout(self)
        table = QTableWidget()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns)

        for i, row in df.iterrows():
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(value)))

        layout.addWidget(table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

# Main GUI Application Class
class MachineVisionApp(QMainWindow):
    def start_local_server(self):
        import subprocess
        import sys
        import os
        templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
        python_exe = sys.executable
        try:
            subprocess.Popen([
                python_exe, '-m', 'http.server', '5000', '--bind', '0.0.0.0'
            ], cwd=templates_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Server error: {e}")

    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.db_manager = DatabaseManager()
        self.ocr_manager = OCRManager()
        self.excel_manager = ExcelManager()
        self.cameras = {}
        self.camera_frames = {}
        self.camera_labels = {}

        # Remove automatic timer processing
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self.process_ocr)
        self.ocr_interval = 1000  # Keep for reference but won't be used automatically

        self.init_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.apply_dark_styles()
        self.setup_cameras()

    def init_ui(self):
        self.setWindowTitle("Machine Vision System - Professional")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Camera display area
        camera_widget = QWidget()
        camera_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        camera_grid = QGridLayout(camera_widget)
        camera_grid.setSpacing(10)

        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555; border-radius: 5px;")
            frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            frame.setMinimumSize(300, 250)

            layout = QVBoxLayout(frame)
            layout.setContentsMargins(1, 1, 1, 1)
            layout.setSpacing(10)

            title = QLabel(f"Camera {i+1}")
            title.setAlignment(Qt.AlignTop)
            title.setFont(QFont('Arial', 12, QFont.Bold))
            title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            layout.addWidget(title)

            camera_label = QLabel("No Signal")
            camera_label.setAlignment(Qt.AlignCenter)
            camera_label.setStyleSheet("color: #888; background: #222; border: none;")
            camera_label.setMinimumSize(280, 200)
            camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            camera_label.setScaledContents(True)
            layout.addWidget(camera_label, stretch=1)

            self.camera_labels[i] = camera_label

            if i < 2:
                camera_grid.addWidget(frame, i, 0)
            else:
                camera_grid.addWidget(frame, 0, 1, 2, 1)

        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_widget.setMinimumWidth(350)
        right_widget.setMaximumWidth(450)
        right_layout = QVBoxLayout(right_widget)

        control_panel = self.create_control_panel()
        right_layout.addWidget(control_panel)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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

        indicator_widget = self.create_status_indicators()
        right_layout.addWidget(indicator_widget)

        main_layout.addWidget(camera_widget, 3)
        main_layout.addWidget(right_widget, 1)

    def create_control_panel(self):
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.StyledPanel)
        control_panel.setStyleSheet("background-color: #404040; border: 1px solid #666; border-radius: 5px; padding: 10px;")
        control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        layout = QVBoxLayout(control_panel)

        entry_label = QLabel("Enter Barcode / Product Code:")
        entry_label.setFont(QFont('Arial', 10, QFont.Bold))
        entry_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(entry_label)

        self.entry_box = QLineEdit()
        self.entry_box.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 3px;
                color: #ffffff;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        layout.addWidget(self.entry_box)

        button_layout1 = QHBoxLayout()
        self.start_btn = self.create_button("Start", "#28a745")
        self.stop_btn = self.create_button("Stop", "#dc3545")
        self.reset_btn = self.create_button("Reset", "#6c757d")
        self.check_btn = self.create_button("Check", "#0078d4")  # New Check button

        for btn in [self.start_btn, self.stop_btn, self.reset_btn, self.check_btn]:
            button_layout1.addWidget(btn)
        layout.addLayout(button_layout1)

        button_layout2 = QHBoxLayout()
        self.database_btn = self.create_button("Database", "#6c757d")
        self.web_btn = self.create_button("Web View", "#17a2b8")

        for btn in [self.database_btn, self.web_btn]:
            button_layout2.addWidget(btn)
        layout.addLayout(button_layout2)

        self.setup_button_connections()

        return control_panel

    def create_button(self, text, color):
        btn = QPushButton(text)
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
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """)
        return btn

    def create_status_indicators(self):
        indicator_widget = QWidget()
        indicator_layout = QHBoxLayout(indicator_widget)

        fail_label = QLabel("FAIL:")
        fail_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.fail_indicator = QFrame()
        self.fail_indicator.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")
        self.fail_indicator.setFixedSize(60, 60)

        pass_label = QLabel("PASS:")
        pass_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.pass_indicator = QFrame()
        self.pass_indicator.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")
        self.pass_indicator.setFixedSize(60, 60)

        indicator_layout.addWidget(fail_label)
        indicator_layout.addWidget(self.fail_indicator)
        indicator_layout.addStretch()
        indicator_layout.addWidget(pass_label)
        indicator_layout.addWidget(self.pass_indicator)

        return indicator_widget

    def setup_cameras(self):
        for i in range(3):
            camera = CameraManager(i)
            camera.frame_ready.connect(self.update_camera_display)
            camera.start()
            self.cameras[i] = camera

    def update_camera_display(self, camera_id, frame):
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)

            scaled_pixmap = pixmap.scaled(
                self.camera_labels[camera_id].size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.camera_labels[camera_id].setPixmap(scaled_pixmap)
            self.camera_frames[camera_id] = frame
        except Exception as e:
            print(f"Display update error for camera {camera_id}: {e}")

    def setup_button_connections(self):
        self.start_btn.clicked.connect(self.start_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
        self.reset_btn.clicked.connect(self.reset_system)
        self.database_btn.clicked.connect(self.open_database_view)
        self.web_btn.clicked.connect(self.open_web_view)
        self.check_btn.clicked.connect(self.check_and_process_ocr)  # New connection

    def check_and_process_ocr(self):
        """Process OCR on demand when Check button is clicked - FIXED VALIDATION"""
        product_code = self.entry_box.text().strip()
        if not product_code:
            self.result_box.append("Please enter a product code before checking.")
            self.light_result_indicator("fail")
            return

        ocr_results = {}
        img_folder = "images"
        os.makedirs(img_folder, exist_ok=True)
        image_files = []

        # Process each camera
        for i in range(3):
            frame = self.camera_frames.get(i)
            text = ""
            if frame is not None:
                text = self.ocr_manager.read_text(frame)
            else:
                text = "No feed"
            ocr_results[i] = text

        # NEW VALIDATION LOGIC - FIXED
        validation_result = "FAIL"
        any_camera_passed = False

        print(f"DEBUG: Product code: '{product_code}'")
        print(f"DEBUG: OCR results: {ocr_results}")

        # Check each camera
        for i, text in ocr_results.items():
            print(f"DEBUG: Checking camera {i+1}: '{text}'")

            # Skip cameras with no feed or empty text
            if text == "" or text == "No feed":
                print(f"DEBUG: Camera {i+1} skipped (no feed or empty)")
                continue

            # Convert to uppercase for case-insensitive comparison
            text_upper = text.upper()
            product_code_upper = product_code.upper()

            # Check if this camera found any of the required keywords
            has_inner = "INNER" in text_upper
            has_outer = "OUTER" in text_upper  
            has_product_code = product_code_upper in text_upper

            print(f"DEBUG: Camera {i+1} - INNER: {has_inner}, OUTER: {has_outer}, Product: {has_product_code}")

            camera_found_keyword = has_inner or has_outer or has_product_code

            if camera_found_keyword:
                any_camera_passed = True
                print(f"DEBUG: Camera {i+1} PASSED! Setting validation to PASS")
                break  # At least one camera passed, we can stop checking

        # Set result based on whether any camera passed
        if any_camera_passed:
            validation_result = "PASS"
        else:
            validation_result = "FAIL"

        print(f"DEBUG: Final validation result: {validation_result}")

        # Only save images if validation fails
        save_img = ""
        if validation_result == "FAIL":
            for i in range(3):
                frame = self.camera_frames.get(i)
                if frame is not None:
                    img_file = os.path.join(img_folder, f"{product_code}_cam{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    cv2.imwrite(img_file, frame)
                    image_files.append(img_file)
            save_img = image_files[0] if image_files else ""
        else:  
            image_files = ["", "", ""]

        # Display results
        display_txt = f"\nProduct Code: {product_code}\n"
        for i, txt in ocr_results.items():
            display_txt += f"Camera {i+1}: {txt}\n"
        display_txt += f"Status: {validation_result}\n"
        if validation_result == "FAIL" and save_img:
            display_txt += f"Images saved to: {img_folder}\n"
        elif validation_result == "PASS":
            display_txt += "No images saved (PASS result)\n"

        self.result_box.append(display_txt)

        # Save to database and Excel
        product_id = self.db_manager.insert_product(
            product_code,
            ocr_results.get(0, ""),
            ocr_results.get(1, ""),
            ocr_results.get(2, ""),
            validation_result,
            save_img
        )

        self.excel_manager.append_data(
            product_id,
            product_code,
            ocr_results.get(0, ""),
            ocr_results.get(1, ""),
            ocr_results.get(2, ""),
            validation_result
        )

        self.light_result_indicator("pass" if validation_result == "PASS" else "fail")

    def check_product(self):
        product_code = self.entry_box.text().strip()
        if not product_code:
            self.result_box.append("Please enter a product code to check in the database.")
            self.light_result_indicator("fail")
            return

        result = self.db_manager.search_product(product_code)
        if result:
            validated = result[6] if len(result) >= 7 else ''
            image_path = result[7] if len(result) >= 8 else ''
            result_text = f"Product code: {product_code}\nStatus: {validated}\n"
            self.result_box.append(result_text)

            if image_path and os.path.exists(image_path):
                pix = QPixmap(image_path).scaled(180, 140, Qt.KeepAspectRatio)
                img_lbl = QLabel()
                img_lbl.setPixmap(pix)
                self.result_box.append(f"[Image loaded: {image_path}]")

            self.light_result_indicator("pass" if validated.upper() == "PASS" else "fail")
        else:
            self.result_box.append(f"No results found for product code: {product_code}")
            self.light_result_indicator("fail")

    def start_processing(self):
        self.processing_timer.start(self.ocr_interval)
        self.statusBar().showMessage("Started OCR auto-processing (every 1 second)")
        self.result_box.append("Started OCR auto-processing...")

    def process_ocr(self):
        """Original OCR processing method - FIXED VALIDATION"""
        product_code = self.entry_box.text().strip()
        ocr_results = {}
        img_folder = "images"
        os.makedirs(img_folder, exist_ok=True)
        image_files = []

        # Process each camera
        for i in range(3):
            frame = self.camera_frames.get(i)
            text = ""
            if frame is not None:
                text = self.ocr_manager.read_text(frame)
                img_file = os.path.join(img_folder, f"{product_code}_cam{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                cv2.imwrite(img_file, frame)
                image_files.append(img_file)
            else:
                text = "No feed"
                image_files.append("")
            ocr_results[i] = text

        # NEW VALIDATION LOGIC - FIXED (same as check_and_process_ocr)
        validation_result = "FAIL"
        any_camera_passed = False

        # Check each camera
        for i, text in ocr_results.items():
            # Skip cameras with no feed or empty text
            if text == "" or text == "No feed":
                continue

            # Convert to uppercase for case-insensitive comparison
            text_upper = text.upper()
            product_code_upper = product_code.upper()

            # Check if this camera found any of the required keywords
            has_inner = "INNER" in text_upper
            has_outer = "OUTER" in text_upper  
            has_product_code = product_code_upper in text_upper

            camera_found_keyword = has_inner or has_outer or has_product_code

            if camera_found_keyword:
                any_camera_passed = True
                break  # At least one camera passed, we can stop checking

        # Set result based on whether any camera passed
        if any_camera_passed:
            validation_result = "PASS"
        else:
            validation_result = "FAIL"

        self.light_result_indicator("pass" if validation_result == "PASS" else "fail")

        # Display results
        display_txt = f"\nProduct Code: {product_code}\n"
        for i, txt in ocr_results.items():
            display_txt += f"Camera {i+1}: {txt}\n"
        display_txt += f"Status: {validation_result}\n"
        self.result_box.append(display_txt)

        save_img = next((img for (i, img) in enumerate(image_files) if ocr_results[i] not in ["", "No feed"]), "")
        
        product_id = self.db_manager.insert_product(
            product_code,
            ocr_results.get(0, ""),
            ocr_results.get(1, ""),
            ocr_results.get(2, ""),
            validation_result,
            save_img
        )

        self.excel_manager.append_data(
            product_id,
            product_code,
            ocr_results.get(0, ""),
            ocr_results.get(1, ""),
            ocr_results.get(2, ""),
            validation_result
        )

    def stop_processing(self):
        self.processing_timer.stop()
        self.result_box.append("Stopped OCR auto-processing.")
        self.statusBar().showMessage("Stopped OCR auto-processing.")

    def reset_system(self):
        self.processing_timer.stop()
        self.entry_box.clear()
        self.result_box.clear()
        self.excel_manager.create_excel_file()
        self.light_result_indicator("reset")
        self.statusBar().showMessage("New Excel file started.")
        self.result_box.append("System reset: started a new Excel record.")

    def open_database_view(self):
        df = self.db_manager.get_all_products()
        dialog = DatabaseViewDialog(df, self)
        dialog.exec_()

    def open_web_view(self):
        import webbrowser
        import time
        self.start_local_server()
        time.sleep(1)
        webbrowser.open('http://localhost:5000/index.html')

    def light_result_indicator(self, status):
        if status == "pass":
            self.pass_indicator.setStyleSheet(
                "background-color: #28a745; border: 2px solid #1e7e34; border-radius: 5px;"
            )
            self.fail_indicator.setStyleSheet(
                "background-color: #495057; border: 2px solid #343a40; border-radius: 5px;"
            )
        elif status == "fail":
            self.fail_indicator.setStyleSheet(
                "background-color: #dc3545; border: 2px solid #c82333; border-radius: 5px;"
            )
            self.pass_indicator.setStyleSheet(
                "background-color: #495057; border: 2px solid #343a40; border-radius: 5px;"
            )
        else:
            self.pass_indicator.setStyleSheet(
                "background-color: #495057; border: 2px solid #343a40; border-radius: 5px;"
            )
            self.fail_indicator.setStyleSheet(
                "background-color: #495057; border: 2px solid #343a40; border-radius: 5px;"
            )

    def setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('View')
        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # About menu
        about_menu = menubar.addMenu('About')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('About')
        layout = QVBoxLayout(dialog)

        label = QLabel()
        label.setTextFormat(Qt.RichText)
        label.setOpenExternalLinks(True)
        label.setText("""
        <h2>Machine Vision OCR System</h2>
        <p><b>Professional OCR and validation system</b></p>
        <p><b>Version:</b> 2.0 - FIXED VALIDATION</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Multi-camera OCR processing</li>
        <li>Real-time validation with PASS/FAIL indicators</li>
        <li>Database storage and Excel export</li>
        <li>Fixed validation logic: PASS if any camera finds INNER, OUTER, or Product Code</li>
        </ul>
        """)
        layout.addWidget(label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()

    def setup_statusbar(self):
        self.statusBar().showMessage("System Ready")

    def apply_dark_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555;
            }
        """)

    def closeEvent(self, event):
        for camera in self.cameras.values():
            camera.stop()
        event.accept()

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
    
    window = MachineVisionApp()
    window.show()
    
    sys.exit(app.exec_())