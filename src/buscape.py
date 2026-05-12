import cv2
import pytesseract
import json
import re
import os

class rodri:
    def __init__(self, coords_json):
        full_coords_path = os.path.abspath(os.path.expanduser(coords_json))
        with open(full_coords_path, 'r') as f:
            self.config = json.load(f)
        self.zones = self.config['coordinates']

    def enhance_image(self, roi):
        """Standard Pitik Sharpening: Upscale + Unsharp Mask"""
        width = int(roi.shape[1] * 2)
        height = int(roi.shape[0] * 2)
        upscaled = cv2.resize(roi, (width, height), interpolation=cv2.INTER_CUBIC)
        
        # Nililinaw ang edges para sa Tesseract
        gaussian = cv2.GaussianBlur(upscaled, (0, 0), 2.0)
        sharpened = cv2.addWeighted(upscaled, 1.5, gaussian, -0.5, 0)
        return sharpened

    def sanitize_amounts(self, amt_str):
        """Nililinis ang OCR string para maging valid float list"""
        raw_list = re.split(r'\s+|\n', amt_str)
        clean_list = []
        for val in raw_list:
            # Alisin lahat except numbers at decimal point
            clean_val = re.sub(r'[^0-9.]', '', val.replace(',', ''))
            if clean_val:
                try:
                    clean_list.append(float(clean_val))
                except ValueError:
                    continue
        return clean_list

    def extract_data(self, image_path):
        """Main workflow: Resize -> Zone Crop -> Enhance -> OCR"""
        full_image_path = os.path.abspath(os.path.expanduser(image_path))
        img = cv2.imread(full_image_path)
        
        if img is None:
            raise FileNotFoundError(f"Hindi mabasa ang image sa: {full_image_path}")

        # OPTION A: Standarized Resize (Crucial for Coord matching)
        img = cv2.resize(img, (1000, 1400), interpolation=cv2.INTER_LANCZOS4)
        
        raw_results = {}
        for field, pos in self.zones.items():
            y1, y2 = pos['y']
            x1, x2 = pos['x']
            
            roi = img[y1:y2, x1:x2]
            enhanced = self.enhance_image(roi)
            
            # PSM 6 for multiline/blocks, PSM 7 logic is handled by specific field types
            psm_config = '--psm 6'
            
            text = pytesseract.image_to_string(enhanced, config=psm_config).strip()
            raw_results[field] = text

        return self.clean_output(raw_results)

    def clean_output(self, raw):
        """Post-processing: Splitting fees, ORs, and aligning data"""
        processed = {}
        
        # 1. General Cleaning (Replace newlines with spaces for single-field data)
        for field, value in raw.items():
            if field not in ['fee_type', 'fee_amts', 'official_receipt_num_s', 'official_receipt_date_s']:
                processed[field] = value.replace('\n', ' ').strip()
            else:
                processed[field] = value # Keep raw for splitting

        # 2. Fee Breakdown Logic
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

        # 3. Official Receipt (OR) Logic
        raw_or_nums = processed.get('official_receipt_num_s', '')
        raw_or_dates = processed.get('official_receipt_date_s', '')

        # OR Numbers: Split by any whitespace
        or_numbers = [n.strip() for n in re.split(r'\s+', raw_or_nums) if n.strip()]
        
        # OR Dates: Use the block-based Regex pattern
        date_pattern = r'[A-Z][a-z]{2,3}\.?\s\d{1,2},?\s20\d{2}'
        or_dates = re.findall(date_pattern, raw_or_dates)
        or_dates = [d.strip() for d in or_dates]

        # Horizontal alignment fallback
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
        
        # Clean up temporary raw fields to keep the dictionary clean
        fields_to_remove = ['fee_type', 'fee_amts', 'official_receipt_num_s', 'official_receipt_date_s']
        for f in fields_to_remove:
            if f in processed: del processed[f]

        return processed