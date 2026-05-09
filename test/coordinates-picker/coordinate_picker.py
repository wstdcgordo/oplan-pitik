# This script allows you to click and drag on an image to select zones, and it will print the coordinates in the console. The red boxes will stay on the screen as you select new zones, while a green box will show the current selection in real-time. You can press 's' to save the coordinates (or just copy them from the console into your JSON file) and 'q' to quit the application.

import cv2  # type: ignore[reportMissingImports]

img = cv2.imread('[put your own image path here]')
img = cv2.resize(img, (1000, 1400)) # type: ignore[reportMissingImports]
clone = img.copy()

original_img = cv2.resize(img, (1000, 1400))

# State variables
drawing = False 
ix, iy = -1, -1
cx, cy = -1, -1

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, cx, cy, drawing, original_img

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        cx, cy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cx, cy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        # PERMANENTLY draw the rectangle on original_img when finished
        cv2.rectangle(original_img, (ix, iy), (x, y), (0, 0, 255), 2)
        
        # Calculate coordinates for your OCR script
        y1, y2 = sorted([iy, y])
        x1, x2 = sorted([ix, x])
        print(f"Locked Zone: y1={y1}, y2={y2}, x1={x1}, x2={x2}")

cv2.namedWindow("BPLS Mapper")
cv2.setMouseCallback("BPLS Mapper", draw_rectangle)

print("Mapping Tool Ready:")
print("- Drag to select. Red boxes will STAY on the screen.")
print("- Press 's' to SAVE (or just copy from console).")
print("- Press 'q' to QUIT.")

while True:
    # Create a 'frame' copy for the live green line
    frame = original_img.copy()

    if drawing:
        # Draw the 'live' green box while moving
        cv2.rectangle(frame, (ix, iy), (cx, cy), (0, 255, 0), 2)

    cv2.imshow("BPLS Mapper", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()