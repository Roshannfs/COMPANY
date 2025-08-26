import cv2
import imutils
from imutils import perspective
import numpy as np

def check_contour_inside_reference(contour, reference_contour):
    """Check if the detected contour fits inside the reference contour"""
    try:
        x1, y1, w1, h1 = cv2.boundingRect(contour)
        x2, y2, w2, h2 = cv2.boundingRect(reference_contour)
        fits_inside = (x1 >= x2 and y1 >= y2 and 
                       x1 + w1 <= x2 + w2 and y1 + h1 <= y2 + h2)
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

def add_reference_shape_from_image(reference_image_path):
    ref_img = cv2.imread(reference_image_path, cv2.IMREAD_GRAYSCALE)
    if ref_img is None:
        return None
    _, thresh = cv2.threshold(ref_img, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        return max(contours, key=cv2.contourArea)
    return None

KNOWN_WIDTH = 14 / 362  # Reference object width in cm
cam = cv2.VideoCapture(1)

cv2.namedWindow("Measurement", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Measurement", 800, 600)

if not cam.isOpened():
    print("Cannot open camera")
    exit()

pixelsPerMetric = None

# Use only one reference image and name
reference_image_path = r"C:\roshan\E.T\E.T\company_project\front.png"
reference_box = add_reference_shape_from_image(reference_image_path)
reference_name = "Object 1"

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame")
        break

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

            # Calculate midpoints for measurements
            tltrX, tltrY = (tl[0] + tr[0]) * 0.5, (tl[1] + tr[1]) * 0.5
            blbrX, blbrY = (bl[0] + br[0]) * 0.5, (bl[1] + br[1]) * 0.5
            tlblX, tlblY = (tl[0] + bl[0]) * 0.5, (tl[1] + bl[1]) * 0.5
            trbrX, trbrY = (tr[0] + br[0]) * 0.5, (tr[1] + br[1]) * 0.5

            dA = np.linalg.norm([tltrX - blbrX, tltrY - blbrY])
            dB = np.linalg.norm([tlblX - trbrX, tlblY - trbrY])

            if pixelsPerMetric is None:
                pixelsPerMetric = dB * KNOWN_WIDTH
                pixelsPerMetrich = dA * KNOWN_WIDTH
            else:
                pixelsPerMetrich = dA * KNOWN_WIDTH

            width = pixelsPerMetric
            height = pixelsPerMetrich

            overlay = image.copy()
            if reference_box is not None:
                ref_img = cv2.imread(reference_image_path, cv2.IMREAD_GRAYSCALE)
                if ref_img is not None:
                    ref_h, ref_w = ref_img.shape
                    img_h, img_w = image.shape[:2]
                    scale_x = img_w / ref_w * 0.55
                    scale_y = img_h / ref_h * 0.9
                    ref_box_reshaped = reference_box.reshape(-1, 2).astype("float")
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
                    fits_inside = check_contour_inside_reference(c, ref_box_scaled)
                else:
                    fits_inside = False
            else:
                fits_inside = False

            if fits_inside:
                status_text = "Correct Dimension: " + reference_name
                status_color = (0, 128, 0)
                cv2.fillPoly(overlay, [c], color=(0, 255, 0))
                cv2.line(overlay, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)), (255, 0, 0), 2)
                cv2.line(overlay, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)), (0, 0, 255), 2)
                cv2.putText(overlay, "{:.2f}cm".format(height),
                            (int(tltrX) - 40, int(tltrY)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                cv2.putText(overlay, "{:.2f}cm".format(width),
                            (int(trbrX), int(trbrY) + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                status_text = "Not Correct Dimension"
                status_color = (139, 0, 0)
                cv2.fillPoly(overlay, [c], color=(0, 0, 255))

            cv2.putText(overlay, status_text, (int(tl[0]), int(tl[1]) - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

            alpha = 0.6
            image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
            cv2.drawContours(image, [box_points.astype("int")], -1, status_color, 2)

    cv2.imshow("Measurement", image)
    if cv2.waitKey(1) == 27:
        break

cam.release()