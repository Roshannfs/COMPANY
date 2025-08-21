import cv2
import easyocr
import pandas as pd
from datetime import datetime
import time
import os

# Settings
interval = 5  # seconds between captures

# Get today's date for filename
today_str = datetime.now().strftime("%d-%m-%Y")
excel_file = f"product_info_{today_str}.xlsx"

# OCR Reader
reader = easyocr.Reader(['en'], gpu=False)  # set gpu=True if you have CUDA

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open camera")

# Create Excel if not exists, else load and continue count
if os.path.exists(excel_file):
    df = pd.read_excel(excel_file)
    if not df.empty and "no of product" in df.columns:
        count = int(df["no of product"].max()) + 1
    else:
        df = pd.DataFrame(columns=["no of product", "time", "info"])
        df.to_excel(excel_file, index=False)
        count = 1
else:
    df = pd.DataFrame(columns=["no of product", "time", "info"])
    df.to_excel(excel_file, index=False)
    count = 1

last_capture_time = 0

print(f"Saving to file: {excel_file}")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time.time()

    # Process every N seconds
    if current_time - last_capture_time >= interval:
        last_capture_time = current_time

        # Run OCR
        results = reader.readtext(frame)

        # If no text detected, keep empty
        if not results:
            text_detected = ""
        else:
            # Join detected texts into one string
            text_detected = " | ".join([text for (_, text, conf) in results])

        # Current time in HH:MM:SS
        now_time = datetime.now().strftime("%H:%M:%S")

        # Append row
        new_row = {"no of product": count, "time": now_time, "info": text_detected}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Save to Excel
        df.to_excel(excel_file, index=False)

        print(f"[{now_time}] Capture #{count} saved → {text_detected}")
        count += 1

    # Show camera feed
    cv2.imshow("Live Camera OCR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
