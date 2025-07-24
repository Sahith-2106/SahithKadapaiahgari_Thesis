import json
import cv2
import pytesseract
import numpy as np
import os
from pathlib import Path
import img2pdf

def process_single_image(image_path, json_path, output_path):
    # 1) Load JSON with bounding boxes
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2) Load image using OpenCV
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not read image: {image_path}")
        return

    boxes = data.get("boxes", [])
    results = []

    # 3) Process each bounding box
    for i, box in enumerate(boxes):
        coords = box["coordinate"]  # [x1, y1, x2, y2]
        x1, y1, x2, y2 = map(int, coords)
        crop = image[y1:y2, x1:x2]  # Crop image based on the coordinates

        # SPECIAL HANDLING FOR PAGE NUMBERS
        if box.get("label") == "berufsnummer" or box.get("label") == "profession_title" or box.get("label") == "year" or box.get("label") == "photo_credits":
            # Enhanced processing for page numbers
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Try multiple OCR configurations
            for config in ['--psm 7','--psm 8','--psm 10']:
                text = pytesseract.image_to_string(thresh, lang='deu', config=config).strip()
                if text:
                    break
        elif box.get("label") == "credits" or box.get("label") == "copyright" or box.get("label") == "disclaimer" or box.get("label") == "publisher_info" or box.get("label") == "imprint" or box.get("label") == "order_number":
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Try multiple OCR configurations
            for config in ['--psm 6','--psm 7','--psm 8','--psm 10','-c tessedit_char_whitelist=0123456789']:
                text = pytesseract.image_to_string(thresh, lang='deu', config=config).strip()
                if text:
                    break
            

        

        elif box.get("label") == "page_number":
            # Convert coordinates to integers
            x1, y1, x2, y2 = map(int, coords)
            
            # Debug: Save the original crop
            debug_dir = "debug_page_numbers"
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(f"{debug_dir}/original_{i}.png", image[y1:y2, x1:x2])
            
            # Try multiple approaches:
            approaches = []
            
            # Approach 1: Simple thresholding
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            approaches.append(thresh1)
            
            # Approach 2: Adaptive thresholding
            thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY_INV, 11, 2)
            approaches.append(thresh2)
            
            # Approach 3: Erosion to remove small noise
            kernel = np.ones((2,2), np.uint8)
            eroded = cv2.erode(thresh1, kernel, iterations=1)
            approaches.append(eroded)
            
            # Try OCR with each approach
            text = ""
            for idx, approach in enumerate(approaches):
                cv2.imwrite(f"{debug_dir}/approach_{i}_{idx}.png", approach)
                
                # Try different PSM modes
                for config in ['--psm 10 -c tessedit_char_whitelist=0123456789', 
                              '--psm 7', 
                              '--psm 8']:
                    current_text = pytesseract.image_to_string(approach, config=config).strip()
                    if current_text.isdigit():
                        text = current_text
                        break
                if text:
                    break
            
            # If still not found, try expanding the search area
            if not text:
                # Expand the search area by 20 pixels in each direction
                expanded_coords = [
                    max(0, x1 - 20),
                    max(0, y1 - 20),
                    min(image.shape[1], x2 + 20),
                    min(image.shape[0], y2 + 20)
                ]
                expanded_crop = image[expanded_coords[1]:expanded_coords[3], 
                                     expanded_coords[0]:expanded_coords[2]]
                gray = cv2.cvtColor(expanded_crop, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                text = pytesseract.image_to_string(thresh, config='--psm 10').strip()
                cv2.imwrite(f"{debug_dir}/expanded_{i}.png", expanded_crop)



        
        else:
            # Normal OCR processing for other elements
            text = pytesseract.image_to_string(crop, lang='deu').strip()

        results.append({
            "box_index": i,
            "label": box.get("label", ""),
            "coordinates": coords,
            "ocr_text": text,
            "confidence": box.get("score", None)
        })

    # 4) Sort all results by vertical position (including page numbers)
    results_sorted = sorted(results, key=lambda r: r["coordinates"][1])

    # 5) Prepare final output - page numbers stay with other sections
    output_data = {
        "sections": results_sorted,  # All sections in order, including page numbers
        "footnotes": [r for r in results_sorted if r["label"] == "footnote"]  # Only footnotes here
    }

    # 6) Write the OCR results to a JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Find and print page number info
    page_numbers = [r for r in results_sorted if r["label"] == "pagenumber"]
    if page_numbers:
        print(f"Detected page number(s): {[pn['ocr_text'] for pn in page_numbers]}")
    print(f"Saved output to {output_path}")

def process_folder(input_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all image and JSON files
    files = [f for f in os.listdir(input_folder) if not f.startswith('.')]
    
    # Separate image and JSON files
    image_files = sorted([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))])
    json_files = sorted([f for f in files if f.lower().endswith('.json')])
    
    # Pair them based on filenames (assuming same basename)
    pairs = []
    for img in image_files:
        base = os.path.splitext(img)[0]
        json_file = f"{base}.json"
        if json_file in json_files:
            pairs.append((img, json_file))
    
    # Sort pairs with special handling for front and back
    def sort_key(x):
        name = os.path.splitext(x[0])[0].lower()
        if name == 'front':
            return (0, name)
        elif name == 'back':
            return (2, name)
        else:
            return (1, name)
    
    pairs.sort(key=sort_key)
    
    # Process each pair
    for img_file, json_file in pairs:
        base_name = os.path.splitext(img_file)[0]
        output_file = f"{base_name}_ocr.json"
        
        image_path = os.path.join(input_folder, img_file)
        json_path = os.path.join(input_folder, json_file)
        output_path = os.path.join(output_folder, output_file)
        
        print(f"\nProcessing {img_file} with {json_file}...")
        process_single_image(image_path, json_path, output_path)
    
    # NEW CODE TO CREATE PDF
    # Get all PNG files and sort them in the correct order
    png_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
    
    # Sort the PNG files: front.png, then numeric files, then back.png
    def pdf_sort_key(f):
        name = os.path.splitext(f)[0].lower()
        if name == 'front':
            return (0,)
        elif name == 'back':
            return (2,)
        try:
            return (1, int(name))
        except ValueError:
            return (1, float('inf'), name)  # put non-numeric files after numbered ones
    
    png_files_sorted = sorted(png_files, key=pdf_sort_key)
    
    # Create PDF only if we have PNG files
    if png_files_sorted:
        pdf_path = os.path.join(output_folder, "merged.pdf")
        print(f"\nCreating PDF from {len(png_files_sorted)} images...")
        
        # Convert PNGs to PDF
        with open(pdf_path, "wb") as f:
            # Get full paths to all PNGs in correct order
            image_paths = [os.path.join(input_folder, png) for png in png_files_sorted]
            f.write(img2pdf.convert(image_paths))
        
        print(f"PDF created at {pdf_path}")

# Example usage:
if __name__ == "__main__":
    input_folder = "Path to input folder"
    output_folder = "Path to output folder"
    
    process_folder(input_folder, output_folder)