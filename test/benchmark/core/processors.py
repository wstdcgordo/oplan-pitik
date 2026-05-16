import cv2
import pytesseract
import json
import re
from concurrent.futures import ThreadPoolExecutor

class rodri_bench:
    def __init__(self, coords_path):
        with open(coords_path, 'r') as f:
            self.config = json.load(f)
        self.zones = self.config['coordinates']

    def enhance_image(self, roi):
        width, height = int(roi.shape[1] * 2), int(roi.shape[0] * 2)
        upscaled = cv2.resize(roi, (width, height), interpolation=cv2.INTER_CUBIC)
        gaussian = cv2.GaussianBlur(upscaled, (0, 0), 2.0)
        return cv2.addWeighted(upscaled, 1.5, gaussian, -0.5, 0)

    def sanitize_amounts(self, raw_text):
        clean_text = raw_text.replace(',', '')
        amounts = re.findall(r'\d+\.\d{2}', clean_text)
        return [float(a) for a in amounts]

    def ocr_worker(self, field_data):
        field, roi = field_data
        if field in ['business_id_no', 'business_plate_no']:
            text = pytesseract.image_to_string(roi, config='--psm 6 --oem 3 -l eng preserve_interword_spaces=1').strip()
        else:
            enhanced = self.enhance_image(roi)
            text = pytesseract.image_to_string(enhanced, config='--psm 6 --oem 3 -l eng preserve_interword_spaces=1').strip()
        return field, text

    def clean_output(self, raw):
        processed = {}
        for field, value in raw.items():
            if field not in ['fee_type', 'fee_amts', 'official_receipt_num_s', 'official_receipt_date_s']:
                processed[field] = value.replace('\n', ' ').strip()
            else:
                processed[field] = value 

        fee_names = re.split(r'\n| {2,}', processed.get('fee_type', ''))
        fee_names = [f.strip() for f in fee_names if len(f.strip()) > 2]
        fee_values = self.sanitize_amounts(processed.get('fee_amts', ''))

        fee_list = []
        for i in range(max(len(fee_names), len(fee_values))):
            name = fee_names[i] if i < len(fee_names) else "Unidentified Fee"
            val = fee_values[i] if i < len(fee_values) else 0.0
            fee_list.append({"fee": name, "amount": val})

        processed['fee_breakdown_list'] = fee_list
        processed['total_grand_calc'] = sum(fee_values)

        raw_or_nums = processed.get('official_receipt_num_s', '')
        raw_or_dates = processed.get('official_receipt_date_s', '')
        or_numbers = [n.strip() for n in re.split(r'\s+', raw_or_nums) if n.strip()]
        date_pattern = r'[A-Z][a-z]{2,3}\.?\s\d{1,2},?\s20\d{2}'
        or_dates = re.findall(date_pattern, raw_or_dates)
        or_dates = [d.strip() for d in or_dates]

        if len(or_numbers) > len(or_dates):
            aggressive_dates = [d.strip() for d in re.split(r'\s{2,}', raw_or_dates) if d.strip()]
            if len(aggressive_dates) > len(or_dates):
                or_dates = aggressive_dates

        or_history = []
        for i in range(max(len(or_numbers), len(or_dates))):
            or_history.append({
                "or_number": or_numbers[i] if i < len(or_numbers) else "RECHECK_OR",
                "or_date": or_dates[i] if i < len(or_dates) else "RECHECK_DATE"
            })

        processed['or_history_list'] = or_history
        fields_to_remove = ['fee_type', 'fee_amts', 'official_receipt_num_s', 'official_receipt_date_s']
        for f in fields_to_remove:
            if f in processed: del processed[f]
        return processed

    def extract_data(self, image_path):
        img = cv2.imread(image_path)
        if img is None: return {"error": "Image not found"}
        img = cv2.resize(img, (1000, 1400), interpolation=cv2.INTER_LANCZOS4)
        tasks = []
        for field, pos in self.zones.items():
            y, x = pos['y'], pos['x']
            roi = img[y[0]:y[1], x[0]:x[1]]
            tasks.append((field, roi))
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(self.ocr_worker, tasks))
            raw_results = dict(results)
        return self.clean_output(raw_results)