import os
from PIL import Image

def convert_diagram_to_dark(image_path, output_path):
    if not os.path.exists(image_path):
        print(f"Diagram not found: {image_path}")
        return False
    
    try:
        img = Image.open(image_path).convert("RGBA")
        data = img.getdata()
        
        new_data = []
        # Target dark background: #0e1117 (Streamlit default dark)
        bg_color = (14, 17, 23, 255)
        # Target light text/lines: #e0e6ed
        text_color = (224, 230, 237, 255)
        
        for item in data:
            r, g, b, a = item
            
            # 1. If it's a white or very light background pixel, make it dark blue/gray
            if r > 240 and g > 240 and b > 240:
                new_data.append(bg_color)
            # 2. If it's a black or very dark pixel (lines, text), make it light gray/white
            elif r < 60 and g < 60 and b < 60:
                new_data.append(text_color)
            else:
                # 3. For colored boxes (blue, orange, purple), keep them but boost contrast if needed
                # If they are very light colored, we can darken them slightly to fit dark mode
                # Let's keep them as they are since they are already colorful and will pop on black!
                new_data.append(item)
                
        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"Successfully converted diagram to dark mode: {output_path}")
        return True
    except Exception as e:
        print(f"Error converting diagram: {e}")
        return False

if __name__ == "__main__":
    src_path = r"c:\Users\Tchan\Documents\Base_de_Conhecimento (1)\PROJETOS\02_PORTFOLIO\shadow_fx_terminal\reports\USDT Transaction Approval-2026-05-15-183841.png"
    out_path = r"c:\Users\Tchan\Documents\Base_de_Conhecimento (1)\PROJETOS\02_PORTFOLIO\shadow_fx_terminal\reports\USDT Transaction Approval-2026-05-15-183841_dark.png"
    convert_diagram_to_dark(src_path, out_path)
