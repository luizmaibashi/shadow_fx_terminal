import os
from PIL import Image

def crop_white_header(image_path, crop_height=60):
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return False
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            # Crop the top 'crop_height' pixels
            cropped_img = img.crop((0, crop_height, width, height))
            cropped_img.save(image_path)
            print(f"Successfully cropped top {crop_height}px from {image_path}")
            return True
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False

if __name__ == "__main__":
    reports_dir = "reports"
    screenshots = [
        "streamlit_scanner_red.png",
        "streamlit_scanner_red_coaf.png",
        "streamlit_scanner_green.png"
    ]
    
    for filename in screenshots:
        path = os.path.join(reports_dir, filename)
        crop_white_header(path, crop_height=60)
