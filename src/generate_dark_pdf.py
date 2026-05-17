import os
from PIL import Image

def scale_and_center_image(image_path, canvas_size=(1920, 1080), bg_color=(14, 17, 23)):
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return None
    
    try:
        # Create a new dark canvas
        canvas = Image.new("RGB", canvas_size, bg_color)
        
        with Image.open(image_path) as img:
            # Convert to RGB to ensure PDF compatibility
            img = img.convert("RGB")
            
            # Calculate resize scale to fit within canvas while maintaining aspect ratio
            # Leave a small margin (e.g. 5% on each side)
            max_w = int(canvas_size[0] * 0.94)
            max_h = int(canvas_size[1] * 0.94)
            
            w, h = img.size
            ratio = min(max_w / w, max_h / h)
            
            # Special case: If the image is the Cover (Slide 1), let it fill the canvas
            if "cover" in os.path.basename(image_path).lower():
                ratio = min(canvas_size[0] / w, canvas_size[1] / h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
            else:
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                
            resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Center the resized image on the canvas
            offset_x = (canvas_size[0] - new_w) // 2
            offset_y = (canvas_size[1] - new_h) // 2
            
            canvas.paste(resized_img, (offset_x, offset_y))
            return canvas
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def build_dark_pdf(image_paths, output_pdf_path):
    import fitz
    
    slides = []
    temp_files = []
    
    print("Scaling and centering images on dark canvases...")
    for i, path in enumerate(image_paths):
        slide = scale_and_center_image(path)
        if slide:
            # Save the slide canvas as a temporary lossless PNG
            temp_png = f"temp_slide_{i}.png"
            slide.save(temp_png, "PNG", compress_level=1)
            temp_files.append(temp_png)
            slides.append(temp_png)
            
    if not slides:
        print("No slides were generated.")
        return False
    
    try:
        # Create a new blank PDF document in PyMuPDF
        doc = fitz.open()
        
        print("Embedding PNGs losslessly into PDF pages...")
        for temp_png in slides:
            # Open the temporary PNG using PyMuPDF
            img_doc = fitz.open(temp_png)
            # Convert the image to a PDF page bytes representation losslessly
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            
            # Open the converted PDF bytes as a document page
            slide_pdf = fitz.open("pdf", pdf_bytes)
            # Insert the page into our main document
            doc.insert_pdf(slide_pdf)
            slide_pdf.close()
            
        # Save the finalized PDF with lossless stream compression
        doc.save(output_pdf_path)
        doc.close()
        
        print(f"Successfully generated ultra-crisp lossless dark-mode PDF: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"Error saving PDF via PyMuPDF: {e}")
        return False
    finally:
        # Clean up temporary lossless files
        print("Cleaning up temporary assets...")
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as ex:
                print(f"Error removing temp file {temp_file}: {ex}")


if __name__ == "__main__":
    reports_dir = "reports"
    
    # Ordered list of slides for the LinkedIn Carousel
    slides_list = [
        "linkedin_slide_1_cover.png",
        "USDT Transaction Approval-2026-05-15-183841_dark.png",
        "grafico_irf.png",
        "grafico_correlacao.png",
        "streamlit_scanner_red.png",
        "streamlit_scanner_red_coaf.png",
        "streamlit_scanner_green.png"
    ]
    
    paths = [os.path.join(reports_dir, name) for name in slides_list]
    output_pdf = os.path.join(reports_dir, "Presentation_Dark.pdf")
    
    build_dark_pdf(paths, output_pdf)
