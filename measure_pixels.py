import cv2
import numpy as np
import math
import sys

# Replace with the path to the user's uploaded image with the yellow ez_iso lines
img_path = r"C:\Users\giuli\.gemini\antigravity\brain\592fde2c-58f6-44d9-baa5-c6ddaa6ef215\media__1772478235212.png"

img = cv2.imread(img_path)
if img is None:
    print("Could not load image.")
    sys.exit(-1)

# Yellow color mask (ez_iso lines)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])
mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

# Find lines using Hough Transform
lines = cv2.HoughLinesP(mask, 1, np.pi/180, threshold=40, minLineLength=15, maxLineGap=10)

lengths = []
if lines is not None:
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = math.hypot(x2 - x1, y2 - y1)
        # We only want main lines, ignoring tiny texts or arrows. Let's print out distinct lengths.
        lengths.append((int(length), (x1,y1,x2,y2)))

# Sort by length
lengths.sort(key=lambda x: x[0], reverse=True)

# Merge similar lengths / overlapping segments
merged_lengths = []
for l, coords in lengths:
    if not any(abs(l - ml) < 15 for ml in merged_lengths):
        merged_lengths.append(l)

print("Measured Yellow Line lengths (in pixels):")
print(merged_lengths[:15])

# Expected physical lengths based on screenshot:
# ~7031, 3411, 2149, 1614, 616, 213, 157, 142, 112
