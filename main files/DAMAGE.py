import cv2
import numpy as np
from datetime import datetime

class BrakePadDefectDetector:
    def __init__(self):
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Defect counters
        self.scratch_count = 0
        self.damage_count = 0
        self.dimension_issues = 0
        
        # Expected brake pad dimensions (adjust according to your specific brake pad)
        self.expected_width_range = (182 ,123) # pixels
        self.expected_height_range = (443 ,122)  # pixels
        
    def preprocess_image(self, frame):
        """Preprocess the image for better defect detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply histogram equalization for better contrast
        enhanced = cv2.equalizeHist(blurred)
        
        return gray, enhanced
    
    def detect_scratches(self, enhanced_image, original_frame):
        """Detect scratches using edge detection and morphological operations"""
        # Apply Canny edge detection for scratch detection
        edges = cv2.Canny(enhanced_image, 30, 100)[1]
        
        # Create morphological kernel for scratch detection (elongated)
        kernel_scratch = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 3))
        
        # Apply morphological closing to connect scratch segments
        scratches = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_scratch)
        
        # Find contours for scratches
        contours, _ = cv2.findContours(scratches, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        scratch_detected = False
        for contour in contours:
            area = cv2.contourArea(contour)
            # Filter scratches by area and aspect ratio
            if 50 < area < 2000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Scratches typically have high aspect ratio (long and thin)
                if aspect_ratio > 3 or (1/aspect_ratio > 3):
                    cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.putText(original_frame, 'SCRATCH', (x, y - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    scratch_detected = True
        
        return scratch_detected
    
    def detect_damages(self, enhanced_image, original_frame):
        """Detect general damages using blob detection and contour analysis"""
        # Apply adaptive thresholding to detect dark spots/damages
        adaptive_thresh = cv2.adaptiveThreshold(enhanced_image, 255, 
                                              cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY_INV, 11, 2)
        
        # Remove small noise
        kernel_clean = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_OPEN, kernel_clean)
        
        # Find contours for damages
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        damage_detected = False
        for contour in contours:
            area = cv2.contourArea(contour)
            # Filter damages by area
            if 100 < area < 5000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Damages are typically more circular/square (aspect ratio close to 1)
                if 0.3 < aspect_ratio < 3:
                    cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(original_frame, 'DAMAGE', (x, y - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    damage_detected = True
        
        return damage_detected
    
    def check_dimensions(self, enhanced_image, original_frame):
        """Check brake pad dimensions against expected values"""
        # Find the largest contour (assuming it's the brake pad)
        contours, _ = cv2.findContours(enhanced_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        dimension_issue = False
        if contours:
            # Get the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(largest_contour) > 10000:  # Minimum size threshold
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Check dimensions against expected ranges
                width_ok = self.expected_width_range[0] <= w <= self.expected_width_range[1]
                height_ok = self.expected_height_range[0] <= h <= self.expected_height_range[1]
                
                if not width_ok or not height_ok:
                    dimension_issue = True
                    cv2.rectangle(original_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(original_frame, f'DIM ISSUE: {w}x{h}', (x, y - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
                # Display dimensions
                cv2.putText(original_frame, f'Size: {w}x{h}px', (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return dimension_issue
    
    def run_detection(self):
        """Main detection loop"""
        print("Brake Pad Defect Detection Started")
        print("Press 'q' to quit, 's' to save screenshot, 'r' to reset counters")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Create a copy for processing
            display_frame = frame.copy()
            
            # Preprocess the image
            gray, enhanced = self.preprocess_image(frame)
            
            # Run defect detection algorithms
            scratch_found = self.detect_scratches(enhanced, display_frame)
            damage_found = self.detect_damages(enhanced, display_frame)
            dimension_issue = self.check_dimensions(gray, display_frame)
            
            # Update counters
            if scratch_found:
                self.scratch_count += 1
            if damage_found:
                self.damage_count += 1
            if dimension_issue:
                self.dimension_issues += 1
            
            # Display status information
            status_text = [
                f"Scratches: {self.scratch_count}",
                f"Damages: {self.damage_count}",
                f"Dim Issues: {self.dimension_issues}"
            ]
            
            for i, text in enumerate(status_text):
                cv2.putText(display_frame, text, (10, 60 + i * 25), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Overall quality assessment
            total_defects = self.scratch_count + self.damage_count + self.dimension_issues
            if total_defects == 0:
                quality_status = "GOOD"
                color = (0, 255, 0)
            elif total_defects < 5:
                quality_status = "ACCEPTABLE"
                color = (0, 255, 255)
            else:
                quality_status = "REJECT"
                color = (0, 0, 255)
            
            cv2.putText(display_frame, f"Quality: {quality_status}", (10, 150), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Display the frame
            cv2.imshow('Brake Pad Defect Detection', display_frame)
            cv2.imshow('Enhanced (Gray)', enhanced)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save screenshot with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"brake_pad_inspection_{timestamp}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"Screenshot saved as {filename}")
            elif key == ord('r'):
                # Reset counters
                self.scratch_count = 0
                self.damage_count = 0
                self.dimension_issues = 0
                print("Counters reset")
        
        self.cleanup()
    
    def cleanup(self):
        """Release resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        print("Detection ended")

# Alternative simplified version for basic defect detection
def simple_brake_pad_detection():
    """Simplified version for quick testing"""
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale and enhance
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.equalizeHist(gray)
        
        # Simple edge detection for defects
        edges = cv2.Canny(enhanced, 50, 150)
        
        # Find and mark contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        defect_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 2000:  # Adjust thresholds as needed
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                defect_count += 1
        
        # Display defect count
        cv2.putText(frame, f'Defects: {defect_count}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.imshow('Simple Brake Pad Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Choose which version to run
    print("Choose detection method:")
    print("1. Full Detection System")
    print("2. Simple Detection")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        detector = BrakePadDefectDetector()
        detector.run_detection()
    else:
        simple_brake_pad_detection()
