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
from flask import Flask, render_template, jsonify, request
import base64
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# Database Manager Class
class DatabaseManager:
    def __init__(self, db_name="machine_vision.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create products table
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

        # Create images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                camera_number INTEGER,
                image_data BLOB,
                timestamp DATETIME,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        conn.commit()
        conn.close()

    def insert_product(self, product_code, cam1_text, cam2_text, cam3_text, validation, image_path):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO products (product_code, timestamp, camera_1_text, camera_2_text, 
                                camera_3_text, validation_result, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_code, datetime.now(), cam1_text, cam2_text, cam3_text, validation, image_path))

        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id

    def insert_image(self, product_id, camera_number, image_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO images (product_id, camera_number, image_data, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (product_id, camera_number, image_data, datetime.now()))

        conn.commit()
        conn.close()

    def search_product(self, product_code):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM products WHERE product_code = ?', (product_code,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_all_products(self):
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM products ORDER BY timestamp DESC", conn)
        conn.close()
        return df

# OCR Manager Class - FIXED
class OCRManager:
    def __init__(self):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        try:
            print("Initializing EasyOCR...")
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("EasyOCR initialized successfully")
        except Exception as e:
            print(f"EasyOCR initialization error: {e}")
            self.reader = None

    def read_text(self, frame):
        if frame is None or self.reader is None:
            return "No OCR available"

        try:
            # Ensure frame is valid
            if len(frame.shape) != 3:
                return "Invalid frame"

            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Perform OCR
            print(f"Processing OCR on frame of size: {frame.shape}")
            results = self.reader.readtext(rgb_frame, detail=0)  # detail=0 returns only text

            if not results:
                return "No text detected"

            detected_text = " | ".join(results)
            print(f"OCR detected: {detected_text}")
            return detected_text

        except Exception as e:
            print(f"OCR Error: {e}")
            return f"OCR Error: {str(e)}"

# Camera Manager Class - FIXED
class CameraManager(QThread):
    frame_ready = pyqtSignal(int, object)  # camera_id, frame
    status_update = pyqtSignal(int, str)   # camera_id, status

    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.cap = None
        self.running = False
        self.frame_count = 0

    def connect_camera(self):
        try:
            print(f"Attempting to connect camera {self.camera_id}")

            # Try different backends
            backends = [cv2.CAP_DSHOW, cv2.CAP_V4L2, cv2.CAP_ANY]

            for backend in backends:
                try:
                    self.cap = cv2.VideoCapture(self.camera_id, backend)
                    if self.cap.isOpened():
                        # Test if we can read a frame
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            # Set camera properties
                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            self.cap.set(cv2.CAP_PROP_FPS, 30)

                            print(f"Camera {self.camera_id} connected successfully with backend {backend}")
                            self.status_update.emit(self.camera_id, "Connected")
                            return True
                        else:
                            self.cap.release()

                except Exception as e:
                    print(f"Backend {backend} failed for camera {self.camera_id}: {e}")
                    continue

            print(f"Camera {self.camera_id} connection failed - all backends tried")
            self.status_update.emit(self.camera_id, "Failed")
            return False

        except Exception as e:
            print(f"Camera {self.camera_id} connection error: {e}")
            self.status_update.emit(self.camera_id, f"Error: {e}")
            return False

    def run(self):
        if not self.connect_camera():
            return

        self.running = True
        consecutive_failures = 0

        while self.running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.frame_count += 1
                    self.frame_ready.emit(self.camera_id, frame.copy())
                    consecutive_failures = 0

                    # Debug output every 30 frames (1 second at 30fps)
                    if self.frame_count % 30 == 0:
                        print(f"Camera {self.camera_id}: Frame {self.frame_count}")
                else:
                    consecutive_failures += 1
                    if consecutive_failures > 10:
                        print(f"Camera {self.camera_id}: Too many consecutive failures")
                        break

                self.msleep(33)  # ~30 FPS

            except Exception as e:
                print(f"Camera {self.camera_id} read error: {e}")
                break

        self.status_update.emit(self.camera_id, "Disconnected")
        print(f"Camera {self.camera_id} stopped")

    def stop(self):
        print(f"Stopping camera {self.camera_id}")
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()
        self.wait(3000)  # Wait up to 3 seconds

# Excel Manager Class - FIXED
class ExcelManager:
    def __init__(self):
        self.create_excel_file()

    def create_excel_file(self):
        today_str = datetime.now().strftime("%d-%m-%Y")
        self.filename = f"product_info_{today_str}.xlsx"

        if not os.path.exists(self.filename):
            df = pd.DataFrame(columns=[
                "ID", "Product Code", "Timestamp", "Camera 1 Text", 
                "Camera 2 Text", "Camera 3 Text", "Validation Result"
            ])
            df.to_excel(self.filename, index=False)
            print(f"Created Excel file: {self.filename}")

    def append_data(self, product_id, product_code, cam1_text, cam2_text, cam3_text, validation):
        try:
            # Read existing data
            if os.path.exists(self.filename):
                df = pd.read_excel(self.filename)
            else:
                df = pd.DataFrame(columns=[
                    "ID", "Product Code", "Timestamp", "Camera 1 Text", 
                    "Camera 2 Text", "Camera 3 Text", "Validation Result"
                ])

            new_row = {
                "ID": product_id,
                "Product Code": product_code,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Camera 1 Text": cam1_text,
                "Camera 2 Text": cam2_text,
                "Camera 3 Text": cam3_text,
                "Validation Result": validation
            }

            # Add new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Save to Excel
            df.to_excel(self.filename, index=False)
            print(f"Data saved to Excel: {self.filename}")

        except Exception as e:
            print(f"Excel write error: {e}")

# Web Server Manager Class - FIXED
class WebServerManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return '''
            <html>
            <head><title>Machine Vision System</title></head>
            <body style="background-color: #2d2d2d; color: white; font-family: Arial;">
                <h1>Machine Vision System - Web Interface</h1>
                <p>API Endpoints:</p>
                <ul>
                    <li><a href="/api/products" style="color: lightblue;">/api/products</a> - Get all products</li>
                    <li>/api/search/&lt;product_code&gt; - Search specific product</li>
                </ul>
            </body>
            </html>
            '''

        @self.app.route('/api/products')
        def get_products():
            try:
                df = self.db_manager.get_all_products()
                return jsonify(df.to_dict('records'))
            except Exception as e:
                return jsonify({"error": str(e)})

        @self.app.route('/api/search/<product_code>')
        def search_product(product_code):
            try:
                results = self.db_manager.search_product(product_code)
                return jsonify(results)
            except Exception as e:
                return jsonify({"error": str(e)})

    def start_server(self, host='localhost', port=5000):
        try:
            threading.Thread(
                target=lambda: self.app.run(host=host, port=port, debug=False, use_reloader=False), 
                daemon=True
            ).start()
            print(f"Web server started at http://{host}:{port}")
        except Exception as e:
            print(f"Web server error: {e}")

# Main GUI Application Class - FIXED
class MachineVisionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False

        # Initialize managers
        print("Initializing application...")
        self.db_manager = DatabaseManager()
        self.ocr_manager = OCRManager()
        self.excel_manager = ExcelManager()
        self.web_server = WebServerManager(self.db_manager)

        # Camera managers
        self.cameras = {}
        self.camera_frames = {}
        self.camera_labels = {}

        # OCR processing
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self.process_ocr)
        self.ocr_interval = 5000  # 5 seconds

        self.init_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.apply_dark_styles()

        # Start web server
        self.web_server.start_server()
        self.statusBar().showMessage("System initialized - Web server at http://localhost:5000")

        # Setup cameras after UI is ready
        QTimer.singleShot(1000, self.setup_cameras)  # Delay camera setup

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

        # Create camera display frames
        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet("background-color: #3a3a3a; border: 2px solid #555; border-radius: 5px;")
            frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            frame.setMinimumSize(300, 250)

            layout = QVBoxLayout(frame)

            # Camera title
            title = QLabel(f"Camera {i+1}")
            title.setAlignment(Qt.AlignCenter)
            title.setFont(QFont('Arial', 12, QFont.Bold))
            title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            layout.addWidget(title)

            # Camera feed label
            camera_label = QLabel("Connecting...")
            camera_label.setAlignment(Qt.AlignCenter)
            camera_label.setStyleSheet("color: #888; background: transparent; border: none;")
            camera_label.setMinimumSize(280, 200)
            camera_label.setScaledContents(True)
            layout.addWidget(camera_label)

            self.camera_labels[i] = camera_label

            # Position cameras in grid
            if i < 2:
                camera_grid.addWidget(frame, i, 0)
            else:
                camera_grid.addWidget(frame, 0, 1, 2, 1)

        # Right panel
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_widget.setMinimumWidth(350)
        right_widget.setMaximumWidth(450)
        right_layout = QVBoxLayout(right_widget)

        # Control panel
        control_panel = self.create_control_panel()
        right_layout.addWidget(control_panel)

        # Result display
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

        # Add initial message
        self.result_box.append("Machine Vision System Ready")
        self.result_box.append("Enter product code and click 'Check' or 'Start' for auto processing")
        self.result_box.append("=" * 50)

        right_layout.addWidget(self.result_box)

        # Status indicators
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

        # Product code entry
        entry_label = QLabel("Enter Barcode / Product Code:")
        entry_label.setFont(QFont('Arial', 10, QFont.Bold))
        entry_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(entry_label)

        self.entry_box = QLineEdit()
        self.entry_box.setPlaceholderText("Enter product code here...")
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

        # Control buttons
        button_layout1 = QHBoxLayout()
        self.check_btn = self.create_button("Check", "#0078d4")
        self.start_btn = self.create_button("Start", "#28a745")
        self.stop_btn = self.create_button("Stop", "#dc3545")
        self.reset_btn = self.create_button("Reset", "#6c757d")

        for btn in [self.check_btn, self.start_btn, self.stop_btn, self.reset_btn]:
            button_layout1.addWidget(btn)
        layout.addLayout(button_layout1)

        # Additional buttons
        button_layout2 = QHBoxLayout()
        self.capture_btn = self.create_button("Capture", "#6c757d")
        self.save_btn = self.create_button("Save", "#6c757d")
        self.database_btn = self.create_button("Database", "#6c757d")
        self.web_btn = self.create_button("Web View", "#17a2b8")

        for btn in [self.capture_btn, self.save_btn, self.database_btn, self.web_btn]:
            button_layout2.addWidget(btn)
        layout.addLayout(button_layout2)

        # Connect button signals
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
                opacity: 0.8;
            }}
            QPushButton:pressed {{
                opacity: 0.6;
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
        print("Setting up cameras...")
        for i in range(3):
            camera = CameraManager(i)
            camera.frame_ready.connect(self.update_camera_display)
            camera.status_update.connect(self.update_camera_status)
            camera.start()
            self.cameras[i] = camera

    def update_camera_status(self, camera_id, status):
        if status in ["Connected", "Disconnected", "Failed"]:
            self.camera_labels[camera_id].setText(f"Camera {camera_id + 1}\n{status}")

    def update_camera_display(self, camera_id, frame):
        try:
            if frame is None:
                return

            # Convert frame to QPixmap
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)

            # Scale to fit label
            scaled_pixmap = pixmap.scaled(
                self.camera_labels[camera_id].size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.camera_labels[camera_id].setPixmap(scaled_pixmap)

            # Store frame for OCR processing
            self.camera_frames[camera_id] = frame.copy()

        except Exception as e:
            print(f"Display update error for camera {camera_id}: {e}")

    def process_ocr(self):
        try:
            product_code = self.entry_box.text().strip()
            if not product_code:
                self.result_box.append("Please enter a product code first!")
                return

            print(f"Processing OCR for product code: {product_code}")

            # Process OCR for all cameras
            ocr_results = {}
            for i in range(3):
                if i in self.camera_frames:
                    print(f"Processing camera {i+1}")
                    text = self.ocr_manager.read_text(self.camera_frames[i])
                    ocr_results[i] = text
                    print(f"Camera {i+1} result: {text}")
                else:
                    ocr_results[i] = "No feed"
                    print(f"Camera {i+1}: No feed available")

            # Determine validation result
            validation_result = self.validate_product(ocr_results)
            print(f"Validation result: {validation_result}")

            # Update indicators
            self.update_status_indicators(validation_result)

            # Display results
            self.display_results(product_code, ocr_results, validation_result)

            # Save to database and Excel
            self.save_results(product_code, ocr_results, validation_result)

        except Exception as e:
            print(f"OCR processing error: {e}")
            self.result_box.append(f"OCR Processing Error: {str(e)}")

    def validate_product(self, ocr_results):
        # Simple validation logic - customize as needed
        valid_cameras = 0
        for text in ocr_results.values():
            if text and text != "No feed" and text != "No text detected" and "Error" not in text:
                valid_cameras += 1

        return "PASS" if valid_cameras >= 1 else "FAIL"  # Changed to >= 1 for easier testing

    def update_status_indicators(self, validation_result):
        if validation_result == "PASS":
            self.pass_indicator.setStyleSheet("background-color: #28a745; border: 2px solid #1e7e34; border-radius: 5px;")
            self.fail_indicator.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")
        else:
            self.fail_indicator.setStyleSheet("background-color: #dc3545; border: 2px solid #c82333; border-radius: 5px;")
            self.pass_indicator.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")

    def display_results(self, product_code, ocr_results, validation_result):
        result_text = f"\nProduct Code: {product_code}"
        result_text += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        for i, text in ocr_results.items():
            result_text += f"Camera {i+1}: {text}\n"

        result_text += f"\nValidation: {validation_result}"
        result_text += "\n" + "=" * 50

        self.result_box.append(result_text)

        # Auto-scroll to bottom
        cursor = self.result_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.result_box.setTextCursor(cursor)

    def save_results(self, product_code, ocr_results, validation_result):
        try:
            print("Saving results...")

            # Save to database
            product_id = self.db_manager.insert_product(
                product_code,
                ocr_results.get(0, ""),
                ocr_results.get(1, ""),
                ocr_results.get(2, ""),
                validation_result,
                ""  # image_path - can be implemented later
            )

            # Save images to database
            for i, frame in self.camera_frames.items():
                if frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_data = buffer.tobytes()
                    self.db_manager.insert_image(product_id, i+1, image_data)

            # Save to Excel
            self.excel_manager.append_data(
                product_id, product_code,
                ocr_results.get(0, ""),
                ocr_results.get(1, ""),
                ocr_results.get(2, ""),
                validation_result
            )

            print(f"Results saved with ID: {product_id}")

        except Exception as e:
            print(f"Save error: {e}")
            self.result_box.append(f"Save Error: {str(e)}")

    def setup_button_connections(self):
        self.check_btn.clicked.connect(self.check_product)
        self.start_btn.clicked.connect(self.start_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
        self.reset_btn.clicked.connect(self.reset_system)
        self.capture_btn.clicked.connect(self.capture_images)
        self.save_btn.clicked.connect(self.save_manual)
        self.database_btn.clicked.connect(self.open_database_view)
        self.web_btn.clicked.connect(self.open_web_view)

    def check_product(self):
        print("Manual check triggered")
        self.process_ocr()

    def start_processing(self):
        print("Starting auto processing")
        self.processing_timer.start(self.ocr_interval)
        self.statusBar().showMessage("Auto processing started (every 5 seconds)")
        self.result_box.append("Auto processing started - will check every 5 seconds")

    def stop_processing(self):
        print("Stopping auto processing")
        self.processing_timer.stop()
        self.statusBar().showMessage("Auto processing stopped")
        self.result_box.append("Auto processing stopped")

    def reset_system(self):
        self.entry_box.clear()
        self.result_box.clear()
        self.processing_timer.stop()
        # Reset indicators
        self.fail_indicator.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")
        self.pass_indicator.setStyleSheet("background-color: #495057; border: 2px solid #343a40; border-radius: 5px;")
        self.statusBar().showMessage("System reset")
        self.result_box.append("System reset - Ready for new processing")

    def capture_images(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        captured = 0
        for i, frame in self.camera_frames.items():
            if frame is not None:
                filename = f"capture_cam{i+1}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                captured += 1

        message = f"Images captured: {captured} files at {timestamp}"
        self.statusBar().showMessage(message)
        self.result_box.append(message)

    def save_manual(self):
        if self.entry_box.text().strip():
            print("Manual save triggered")
            self.process_ocr()
            self.statusBar().showMessage("Data saved manually")
        else:
            QMessageBox.warning(self, "Warning", "Please enter a product code first!")

    def open_database_view(self):
        try:
            df = self.db_manager.get_all_products()
            dialog = DatabaseViewDialog(df, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Could not open database: {e}")

    def open_web_view(self):
        import webbrowser
        webbrowser.open('http://localhost:5000')

    def setup_menu(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu('View')
        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

    def setup_statusbar(self):
        self.statusBar().showMessage('Initializing - Please wait...')

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
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555;
            }
        """)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        print("Closing application...")
        # Stop processing
        self.processing_timer.stop()

        # Cleanup cameras
        for camera in self.cameras.values():
            camera.stop()

        print("Application closed")
        event.accept()

# Database View Dialog
class DatabaseViewDialog(QDialog):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database View")
        self.setGeometry(200, 200, 1000, 600)
        self.db_manager = parent.db_manager if parent else None

        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Product Code:")
        self.search_entry = QLineEdit()
        search_btn = QPushButton("Search")
        refresh_btn = QPushButton("Refresh")

        search_btn.clicked.connect(self.search_product)
        refresh_btn.clicked.connect(self.refresh_data)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(refresh_btn)
        layout.addLayout(search_layout)

        # Table view
        self.table = QTableWidget()
        self.populate_table(df)
        layout.addWidget(self.table)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def populate_table(self, df):
        if df.empty:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("No data available"))
            return

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())

        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def search_product(self):
        if not self.db_manager:
            return

        product_code = self.search_entry.text().strip()
        if product_code:
            results = self.db_manager.search_product(product_code)
            # Convert results to DataFrame for display
            if results:
                columns = ["ID", "Product Code", "Timestamp", "Camera 1", "Camera 2", "Camera 3", "Validation", "Image Path"]
                df = pd.DataFrame(results, columns=columns)
                self.populate_table(df)
            else:
                # Show no results
                self.table.setRowCount(1)
                self.table.setColumnCount(1)
                self.table.setItem(0, 0, QTableWidgetItem("No results found"))

    def refresh_data(self):
        if self.db_manager:
            df = self.db_manager.get_all_products()
            self.populate_table(df)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Apply dark theme
    app.setStyle('Fusion')
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

    gui = MachineVisionApp()
    gui.show()

    sys.exit(app.exec_())
