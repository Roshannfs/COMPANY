import cv2
import numpy as np
import math

class DistanceMeasurementTool:
    def __init__(self):
        self.points = []
        self.measurements = []
        self.current_frame = None
        self.original_frame = None
        
    def click_event(self, event, x, y, flags, params):
        """Enhanced mouse callback with multiple measurement support"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            
            if len(self.points) == 1:
                self.draw_point(self.points[0], "Point 1")
                print(f"Point 1 selected: {self.points[0]}")
                
            elif len(self.points) == 2:
                self.draw_point(self.points[1], "Point 2")
                distance = self.calculate_and_draw_distance()
                self.measurements.append({
                    'points': self.points.copy(),
                    'distance': distance
                })
                print(f"Point 2 selected: {self.points[1]}")
                print(f"Measurement #{len(self.measurements)}: {distance:.2f} pixels")
                self.points = []
    
    def draw_point(self, point, label):
        """Draw a point with label"""
        cv2.circle(self.current_frame, point, 8, (0, 0, 255), -1)
        cv2.circle(self.current_frame, point, 12, (255, 255, 255), 2)
        cv2.putText(self.current_frame, label, 
                   (point[0] + 15, point[1] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    def calculate_and_draw_distance(self):
        """Calculate distance and draw measurement"""
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]
        
        # Calculate distance
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Draw line
        cv2.line(self.current_frame, self.points[0], self.points[1], (0, 0, 255), 2)
        
        # Calculate angle for text rotation (optional)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        
        # Midpoint for text
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        
        # Distance text with background
        distance_text = f"{distance:.1f}px"
        text_size = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        
        # Background rectangle
        cv2.rectangle(self.current_frame,
                     (mid_x - text_size[0]//2 - 3, mid_y - text_size[1] - 8),
                     (mid_x + text_size[0]//2 + 3, mid_y + 3),
                     (255, 255, 255), -1)
        cv2.rectangle(self.current_frame,
                     (mid_x - text_size[0]//2 - 3, mid_y - text_size[1] - 8),
                     (mid_x + text_size[0]//2 + 3, mid_y + 3),
                     (0, 0, 255), 1)
        
        # Text
        cv2.putText(self.current_frame, distance_text,
                   (mid_x - text_size[0]//2, mid_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return distance
    
    def display_measurements_info(self):
        """Display measurement history on frame"""
        y_offset = 30
        cv2.putText(self.current_frame, f"Measurements: {len(self.measurements)}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if self.measurements:
            last_measurement = self.measurements[-1]['distance']
            cv2.putText(self.current_frame, f"Last: {last_measurement:.1f}px", 
                       (10, y_offset + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    def run(self):
        """Main execution function"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Creating demo canvas...")
            self.run_with_canvas()
        else:
            print("Using webcam. Controls:")
            print("- Click two points to measure distance")
            print("- Press 'c' to clear all measurements")
            print("- Press 'ESC' to exit")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                self.current_frame = frame.copy()
                self.original_frame = frame.copy()
                
                # Draw all previous measurements
                for measurement in self.measurements:
                    points = measurement['points']
                    cv2.circle(self.current_frame, points[0], 6, (0, 0, 255), -1)
                    cv2.circle(self.current_frame, points[1], 6, (0, 0, 255), -1)
                    cv2.line(self.current_frame, points[0], points[1], (0, 0, 255), 1)
                
                # Add current points if any
                for i, point in enumerate(self.points):
                    self.draw_point(point, f"Point {i+1}")
                
                self.display_measurements_info()
                
                cv2.imshow('Distance Measurement Tool', self.current_frame)
                cv2.setMouseCallback('Distance Measurement Tool', self.click_event)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('c'):  # Clear measurements
                    self.measurements.clear()
                    self.points.clear()
                    print("All measurements cleared!")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Print final summary
        print(f"\nFinal Summary:")
        print(f"Total measurements taken: {len(self.measurements)}")
        for i, measurement in enumerate(self.measurements, 1):
            print(f"Measurement {i}: {measurement['distance']:.2f} pixels")
    
    def run_with_canvas(self):
        """Run with a demo canvas when webcam is not available"""
        self.current_frame = np.ones((600, 800, 3), dtype=np.uint8) * 240
        
        # Add demo content
        cv2.putText(self.current_frame, "Distance Measurement Tool - Demo Mode", 
                   (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(self.current_frame, "Click two points to measure distance", 
                   (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        cv2.putText(self.current_frame, "Press 'c' to clear, ESC to exit", 
                   (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        # Add some reference objects
        cv2.rectangle(self.current_frame, (100, 200), (350, 350), (200, 150, 100), 2)
        cv2.circle(self.current_frame, (600, 300), 100, (100, 150, 200), 2)
        cv2.putText(self.current_frame, "Sample objects for measurement", 
                   (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        cv2.imshow('Distance Measurement Tool', self.current_frame)
        cv2.setMouseCallback('Distance Measurement Tool', self.click_event)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('c'):  # Clear
                self.measurements.clear()
                self.points.clear()
                # Redraw canvas
                self.current_frame = np.ones((600, 800, 3), dtype=np.uint8) * 240
                cv2.putText(self.current_frame, "Distance Measurement Tool - Demo Mode", 
                           (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                cv2.putText(self.current_frame, "Click two points to measure distance", 
                           (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(self.current_frame, "Press 'c' to clear, ESC to exit", 
                           (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
                cv2.rectangle(self.current_frame, (100, 200), (350, 350), (200, 150, 100), 2)
                cv2.circle(self.current_frame, (600, 300), 100, (100, 150, 200), 2)
                cv2.putText(self.current_frame, "Sample objects for measurement", 
                           (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
                cv2.imshow('Distance Measurement Tool', self.current_frame)
                print("Canvas cleared!")

# Run the application
if __name__ == "__main__":
    tool = DistanceMeasurementTool()
    tool.run()
