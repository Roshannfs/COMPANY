import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import cv2
import easyocr
import pandas as pd
from datetime import datetime
import time

class OCRReader:
    def __init__(self, languages=['en'], gpu=False):
        # Disable verbose to avoid progress bar encoding issues
        self.reader = easyocr.Reader(languages, gpu=gpu, verbose=False)
    
    def read_text(self, frame):
        # Convert frame from BGR (OpenCV) to RGB (EasyOCR expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.reader.readtext(rgb_frame)
        if not results:
            return ""
        # Unpack only the second element (text) from each result
        return " | ".join([result[1] for result in results])

class ExcelManager:
    def __init__(self, filename):
        self.filename = filename
        if os.path.exists(self.filename):
            self.df = pd.read_excel(self.filename)
            if not self.df.empty and "no of product" in self.df.columns:
                self.count = int(self.df["no of product"].max()) + 1
            else:
                self.df = pd.DataFrame(columns=["no of product", "time", "info"])
                self.df.to_excel(self.filename, index=False)
                self.count = 1
        else:
            self.df = pd.DataFrame(columns=["no of product", "time", "info"])
            self.df.to_excel(self.filename, index=False)
            self.count = 1
    
    def append_row(self, time_str, info):
        new_row = {"no of product": self.count, "time": time_str, "info": info}
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.df.to_excel(self.filename, index=False)
        self.count += 1

class CameraManager:
    def __init__(self, camera_id=0):
        print("Searching for available cameras...")
        
        self.cap = None
        
        # Try DirectShow first (Windows - most reliable)
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        self.cap = cap
                        print(f"Camera {i} opened successfully with DirectShow")
                        break
                    else:
                        cap.release()
            except:
                continue
        
        # If DirectShow failed, try default backend
        if self.cap is None:
            print("DirectShow failed, trying default backend...")
            for i in range(3):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            self.cap = cap
                            print(f"Camera {i} opened successfully with default backend")
                            break
                        else:
                            cap.release()
                except:
                    continue
        
        if self.cap is None:
            raise RuntimeError("No working camera found. Please check:\n"
                             "1. Camera is connected and powered\n"
                             "2. Camera permissions are enabled in Windows settings\n"
                             "3. No other application is using the camera\n"
                             "4. Camera drivers are properly installed")
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
    
    def read_frame(self):
        ret, frame = self.cap.read()
        return ret, frame
    
    def release(self):
        if self.cap:
            self.cap.release()
            print("Camera released successfully")

class ProductInfoApp:
    def __init__(self, interval=5):
        self.interval = interval
        today_str = datetime.now().strftime("%d-%m-%Y")
        excel_file = f"product_info_{today_str}.xlsx"
        
        print("Initializing OCR Product Info Application...")
        
        try:
            self.camera = CameraManager()
            self.ocr = OCRReader()
            self.excel = ExcelManager(excel_file)
            self.last_capture_time = 0
            print("Application initialized successfully!")
        except RuntimeError as e:
            print(f"Error initializing application: {e}")
            raise
    
    def run(self):
        print(f"Saving to file: {self.excel.filename}")
        print("Application is running...")
        print("- OCR captures every 5 seconds")
        print("- Press 'q' in camera window to quit (if window is available)")
        print("- Press Ctrl+C to quit from terminal")
        
        gui_available = True
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.camera.read_frame()
                if not ret:
                    print("Failed to read frame, retrying...")
                    time.sleep(1)
                    continue
                
                current_time = time.time()
                if current_time - self.last_capture_time >= self.interval:
                    self.last_capture_time = current_time
                    
                    print("Processing frame for OCR...")
                    text_detected = self.ocr.read_text(frame)
                    now_time = datetime.now().strftime("%H:%M:%S")
                    self.excel.append_row(now_time, text_detected)
                    
                    # Save occasional frames to verify camera is working
                    if frame_count < 3:
                        cv2.imwrite(f"camera_test_{frame_count}.jpg", frame)
                        print(f"Test frame saved as camera_test_{frame_count}.jpg")
                        frame_count += 1
                    
                    print(f"[{now_time}] Capture #{self.excel.count-1} saved -> {text_detected}")
                
                # Try to display the camera feed
                if gui_available:
                    try:
                        cv2.imshow("Live Camera OCR", frame)
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            print("Quit key pressed")
                            break
                    except cv2.error as e:
                        print(f"Display window error: {e}")
                        print("Camera is working but display is disabled (running headless)")
                        print("OCR processing will continue normally...")
                        gui_available = False
                        # Remove any existing windows
                        cv2.destroyAllWindows()
                else:
                    # Small delay when running headless to prevent excessive CPU usage
                    time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutdown signal received...")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Cleaning up...")
            self.camera.release()
            cv2.destroyAllWindows()
            print("Application stopped successfully!")

if __name__ == "__main__":
    try:
        app = ProductInfoApp(interval=5)
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        input("Press Enter to exit...")
