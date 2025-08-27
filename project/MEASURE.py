import cv2
import imutils
from imutils import perspective
import numpy as np
import os

class BrakeMeasurement:
    KNOWN_WIDTH = 14 / 362  # Reference object width in cm

    def __init__(self, reference_image_paths):
        self.reference_image_paths = reference_image_paths
        self.reference_names = [os.path.splitext(os.path.basename(path))[0].upper() for path in reference_image_paths]
        self.reference_contours = [self.add_reference_shape_from_image(path) for path in reference_image_paths]
        self.pixelsPerMetric = None
        self.pixelsPerMetrich = None
        self.cam = cv2.VideoCapture(0)
        cv2.namedWindow("Measurement", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Measurement", 800, 600)

    @staticmethod
    def midpoint(x, y):
        return ((x[0] + y[0]) * 0.5, (x[1] + y[1]) * 0.5)

    @staticmethod
    def check_contour_inside_reference(contour, reference_contour):
        try:
            x1, y1, w1, h1 = cv2.boundingRect(contour)
            x2, y2, w2, h2 = cv2.boundingRect(reference_contour)
            fits_inside = (x1 >= x2 and y1 >= y2 and x1 + w1 <= x2 + w2 and y1 + h1 <= y2 + h2)
            points_inside = True
            for point in contour.reshape(-1, 2):
                point_tuple = (float(point[0]), float(point[1]))
                if cv2.pointPolygonTest(reference_contour, point_tuple, False) < 0:
                    points_inside = False
                    break
            return fits_inside and points_inside
        except Exception as e:
            print(f"Error in containment check: {e}")
            return False

    @staticmethod
    def blend_images(image, overlay, alpha):
        return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    @staticmethod
    def add_reference_shape_from_image(reference_image_path):
        ref_img = cv2.imread(reference_image_path, cv2.IMREAD_GRAYSCALE)
        if ref_img is None:
            return None
        _, thresh = cv2.threshold(ref_img, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            return max(contours, key=cv2.contourArea)
        return None

    def process_frame(self, frame):
        image = imutils.resize(frame, width=600)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(blurred, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        if len(cnts) > 0:
            largest_contour = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) >= 100:
                c = largest_contour
                box = cv2.minAreaRect(c)
                box_points = cv2.boxPoints(box)
                box_points = np.array(box_points, dtype="int")
                box_points = perspective.order_points(box_points)
                (tl, tr, br, bl) = box_points
                (tltrX, tltrY) = self.midpoint(tl, tr)
                (blbrX, blbrY) = self.midpoint(bl, br)
                (tlblX, tlblY) = self.midpoint(tl, bl)
                (trbrX, trbrY) = self.midpoint(tr, br)
                dA = np.linalg.norm([tltrX - blbrX, tltrY - blbrY])
                dB = np.linalg.norm([tlblX - trbrX, tlblY - trbrY])
                if self.pixelsPerMetric is None:
                    self.pixelsPerMetric = dB * self.KNOWN_WIDTH
                    self.pixelsPerMetrich = dA * self.KNOWN_WIDTH
                else:
                    self.pixelsPerMetrich = dA * self.KNOWN_WIDTH
                width = self.pixelsPerMetric
                height = self.pixelsPerMetrich

                matching_names = []
                overlay = image.copy()
                for idx, (ref_box, ref_path, ref_name) in enumerate(zip(self.reference_contours, self.reference_image_paths, self.reference_names)):
                    if ref_box is None:
                        continue
                    ref_img = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
                    if ref_img is None:
                        continue
                    ref_h, ref_w = ref_img.shape
                    img_h, img_w = image.shape[:2]
                    scale_x = img_w / ref_w * 0.55
                    scale_y = img_h / ref_h * 0.9
                    ref_box_reshaped = ref_box.reshape(-1, 2).astype("float")
                    ref_box_reshaped[:, 0] *= scale_x
                    ref_box_reshaped[:, 1] *= scale_y
                    min_x, min_y = np.min(ref_box_reshaped, axis=0)
                    max_x, max_y = np.max(ref_box_reshaped, axis=0)
                    offset_x = (img_w - (max_x - min_x)) / 2 - min_x
                    offset_y = (img_h - (max_y - min_y)) / 2 - min_y
                    ref_box_reshaped[:, 0] += offset_x
                    ref_box_reshaped[:, 1] += offset_y
                    ref_box_scaled = ref_box_reshaped.astype("int").reshape(-1, 1, 2)
                    cv2.polylines(overlay, [ref_box_scaled], isClosed=True, color=(255, 255, 0), thickness=3)
                    fits_inside = self.check_contour_inside_reference(c, ref_box_scaled)
                    if fits_inside:
                        matching_names.append(ref_name)

                if matching_names:
                    status_text = "FRONT BRAKE: " + ", ".join(matching_names)
                    status_color = (0, 128, 0)
                    cv2.fillPoly(overlay, [c], color=(0, 255, 0))
                    cv2.line(overlay, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)), (255, 0, 0), 2)
                    cv2.line(overlay, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)), (0, 0, 255), 2)
                    cv2.putText(overlay, "{:.2f}cm".format(height), (int(tltrX) - 40, int(tltrY)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    cv2.putText(overlay, "{:.2f}cm".format(width), (int(trbrX), int(trbrY) + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    status_text = "REAR BRAKE "
                    status_color = (139, 0, 0)
                    cv2.fillPoly(overlay, [c], color=(0, 0, 255))

                cv2.putText(overlay, status_text, (int(tl[0]), int(tl[1]) - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
                alpha = 0.6
                image = self.blend_images(image, overlay, alpha)
                cv2.drawContours(image, [box_points.astype("int")], -1, status_color, 2)
        return image

    def run(self):
        if not self.cam.isOpened():
            print("Cannot open camera")
            return
        while True:
            ret, frame = self.cam.read()
            if not ret:
                print("Failed to grab frame")
                break
            image = self.process_frame(frame)
            cv2.imshow("Measurement", image)
            if cv2.waitKey(1) == 27:
                break
        self.cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    reference_image_paths = [r"C:\github\COMPANY\images\front.png"]
    bm = BrakeMeasurement(reference_image_paths)
    bm.run()
