import cv2
import pytesseract
import json
import os, re

# If Windows user, you may need to specify the tesseract_cmd path like this:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def enhance_for_ocr_color(roi):
    """
    Papalinawin ang image gamit ang scaling at sharpening 
    nang hindi tinatanggal ang kulay.
    """
    width = int(roi.shape[1] * 2)
    height = int(roi.shape[0] * 2)
    upscaled = cv2.resize(roi, (width, height), interpolation=cv2.INTER_CUBIC)
    gaussian_3 = cv2.GaussianBlur(upscaled, (0, 0), 2.0)
    sharpened = cv2.addWeighted(upscaled, 1.5, gaussian_3, -0.5, 0)
    return sharpened

def sanitize_amounts(amt_str):
    """Nililinis ang amount string para maging valid list ng numbers."""
    raw_list = re.split(r'\s+|\n', amt_str)
    clean_list = []
    for val in raw_list:
        clean_val = re.sub(r'[^0-9.]', '', val.replace(',', ''))
        if clean_val:
            try:
                clean_list.append(float(clean_val))
            except ValueError:
                continue
    return clean_list

def test_zonal_ocr(image_path, coords_json):
    full_image_path = os.path.abspath(os.path.expanduser(image_path))
    full_coords_path = os.path.abspath(os.path.expanduser(coords_json))
    print(f"--- 👁️ Project Pitik: Zonal OCR Test (Standardized 1000x1400) ---")
    
    
    img = cv2.imread(full_image_path)
    if img is None:
        print(f"❌ Error: Hindi mabasa ang image sa: {full_image_path}")
        return None
    
    img = cv2.resize(img, (1000, 1400), interpolation=cv2.INTER_LANCZOS4)
    
    try:
        with open(full_coords_path, 'r') as f:
            config = json.load(f)
        zones = config['coordinates']
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return None

    extracted_results = {}
    print(f"Processing: {os.path.basename(full_image_path)}...")
    if not os.path.exists('temp_rois'):
        os.makedirs('temp_rois')
    for field, pos in zones.items():
        y1, y2 = pos['y']
        x1, x2 = pos['x']
        
        roi = img[y1:y2, x1:x2]
        cv2.imwrite(f'temp_rois/{field}.png', roi)
        
        psm_config = '--psm 6'
        roi_enhanced = enhance_for_ocr_color(roi)
        
        text = pytesseract.image_to_string(roi_enhanced, config=psm_config).strip()
        
        if field not in ['fee_type', 'fee_amts']:
            text = text.replace('\n', ' ')
        
        extracted_results[field] = text.strip()
        print(f"🔍 Extracted [{field}]: {text}")
    
    print("\n--- 🛠️ Processing Fee Breakdown ---")
    
    fee_names = re.split(r'\n| {2,}', extracted_results.get('fee_type', ''))
    fee_names = [f.strip() for f in fee_names if len(f.strip()) > 2] # Filter out noise
    
    fee_values = sanitize_amounts(extracted_results.get('fee_amts', ''))
    fee_breakdown = []
    for i in range(max(len(fee_names), len(fee_values))):
        name = fee_names[i] if i < len(fee_names) else "Unidentified Fee"
        val = fee_values[i] if i < len(fee_values) else 0.0
        fee_breakdown.append({"fee": name, "amount": val})
        print(f"   💰 {name}: {val}")

    extracted_results['fee_breakdown_list'] = fee_breakdown
    extracted_results['calculated_total'] = sum(fee_values)
    
    scanned_total = sanitize_amounts(extracted_results.get('total_grand', ''))
    if scanned_total:
        print(f"\n📊 Verification: Calculated({sum(fee_values)}) vs Scanned({scanned_total[0]})")
 
    raw_or_nums = extracted_results.get('official_receipt_num_s', '')
    raw_or_dates = extracted_results.get('official_receipt_date_s', '')
    
    or_numbers = [n.strip() for n in re.split(r'\s+', raw_or_nums) if n.strip()]
    date_pattern = r'[A-Z][a-z]{2,3}\.?\s\d{1,2},?\s20\d{2}'
    
    or_dates = re.findall(date_pattern, raw_or_dates)
    or_dates = [d.strip() for d in or_dates]
    
    if len(or_numbers) > len(or_dates):
        aggressive_dates = [d.strip() for d in re.split(r'\s{2,}', raw_or_dates) if d.strip()]
        if len(aggressive_dates) > len(or_dates):
            or_dates = aggressive_dates
    
    or_history = []
    max_or_rows = max(len(or_numbers), len(or_dates))

    for i in range(max_or_rows):
        num = or_numbers[i] if i < len(or_numbers) else "RECHECK_OR"
        dt = or_dates[i] if i < len(or_dates) else "RECHECK_DATE"
        
        or_history.append({
            "or_number": num,
            "or_date": dt
        })

    extracted_results['or_history_list'] = or_history
    
    print("\n--- 🏁 OCR Test Complete ---")
    return extracted_results

if __name__ == "__main__":
    SAMPLE_IMAGE = "[put your own image path here]" 
    JSON_COORDS = "[put your own coordinate path here].json"

    if os.path.exists(SAMPLE_IMAGE):
        results = test_zonal_ocr(SAMPLE_IMAGE, JSON_COORDS)
        
        print("\nFinal Dictionary for Database Ingest:")
        print(json.dumps(results, indent=4))
    else:
        print(f"⚠️ Pakilagay ang '{SAMPLE_IMAGE}' sa folder na ito para sa test.")