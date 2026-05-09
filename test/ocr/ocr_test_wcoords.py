import cv2
import json
import os

# CONFIGURATION
# Palitan ang path ng image na gusto mong i-map
SAMPLE_IMAGE = os.path.expanduser("[put your own image path here]") 
OUTPUT_JSON = "[put your own coordinate output path here].json"

# State variables
img = cv2.imread(SAMPLE_IMAGE)
if img is None:
    print(f"❌ Error: Hindi mabasa ang {SAMPLE_IMAGE}")
    exit()

# I-standardize ang size para sa consistent coordinates
img = cv2.resize(img, (1000, 1400))
original_img = img.copy()
drawing = False 
ix, iy = -1, -1
cx, cy = -1, -1

# Dito ise-save ang mga coordinates
mapping_data = {"template_name": "Infanta_BPLS_2026", "coordinates": {}}

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, cx, cy, drawing, original_img, mapping_data

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        cx, cy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cx, cy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        y1, y2 = sorted([iy, y])
        x1, x2 = sorted([ix, x])
        
        # UI prompt sa terminal para pangalanan ang zone
        field_name = input(f"Pangalanan ang Zone [y:{y1}-{y2}, x:{x1}-{x2}]: ").strip()
        
        if field_name:
            # I-save sa dictionary
            mapping_data["coordinates"][field_name] = {"y": [y1, y2], "x": [x1, x2]}
            
            # Draw permanent RED box and LABEL on original_img
            cv2.rectangle(original_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(original_img, field_name, (x1, y1-5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            print(f"✅ Saved: {field_name}")
        else:
            print("⚠️ Ignored: Walang pangalan.")

cv2.namedWindow("Pitik Mapper")
cv2.setMouseCallback("Pitik Mapper", draw_rectangle)

print("\n--- 🛠️ Pitik Zonal Mapper Tool ---")
print("1. Drag mouse sa image para gumawa ng box.")
print("2. Sa Terminal, i-type ang field name (hal. business_name) at Enter.")
print("3. Pindutin ang 's' para i-save ang JSON.")
print("4. Pindutin ang 'q' para lumabas.\n")

while True:
    frame = original_img.copy()
    if drawing:
        cv2.rectangle(frame, (ix, iy), (cx, cy), (0, 255, 0), 2)

    cv2.imshow("Pitik Mapper", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord("s"):
        with open(OUTPUT_JSON, "w") as f:
            json.dump(mapping_data, f, indent=4)
        print(f"📂 JSON Saved to: {OUTPUT_JSON}")
    elif key == ord("q"):
        break

cv2.destroyAllWindows()