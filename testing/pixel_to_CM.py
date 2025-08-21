import cv2
import numpy as np
import math

cm = int(input("Enter the known cm: "))
pixels = int(input("Enter the known pixels: "))
ratio = cm / pixels #cm / pixels
pixel_value = int(input("Enter pixel value: "));
distance_cm = pixel_value * ratio
print(distance_cm, "cm")