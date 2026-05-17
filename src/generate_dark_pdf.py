import os
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import fitz

# ─── DESIGN SYSTEM ────────────────────────────────────────────────────────────
BG_COLOR      = (14, 17, 23)      # Streamlit dark background
ACCENT_CYAN   = (0, 212, 255)     # Headline accent
TEXT_WHITE    = (240, 246, 255)   # Primary text
TEXT_LIGHT    = (180, 190, 210)   # Secondary / label text
PILL_BG       = (22, 30, 45, 220) # Semi-transparent dark pill for captions
CANVAS_SIZE   = (1920, 1080)

FONT_BOLD   = "C:/Windows/Fonts/segoeuib.ttf"
FONT_NORMAL = "C:/Windows/Fonts/segoeui.ttf"

# ─── PER-SLIDE METADATA ───────────────────────────────────────────────────────
# Each entry: (slide_number_label, headline, subline)
SLIDE_META = [
    (
        "01 / 07",
        "SHADOW FX TERMINAL",
        "Hedge Legítimo ou Ocultação? A ciência de dados separa o Poupador do Lavador de Dinheiro."
    ),
    (
        "02 / 07",
        "Arquitetura em Cascata",
        "3 barreiras de triagem independentes: Regras BCB → IA para Anomalias → Agente RAG Generativo."
    ),
    (
        "03 / 07",
        "Índice de Risco Fiscal (IRF v2)",
        "Termômetro macroeconômico: detecta picos de dominância fiscal e estresse cambial no Brasil."
    ),
    (
        "04 / 07",
        "Prova Econométrica",
        "A desvalorização do Real precede a corrida ao USDT em 1–4 semanas (Lead-Lag, r = 0.504)."
    ),
    (
        "05 / 07",
        "🔴  Alerta Vermelho — Smurfing Detectado",
        "IA contextual detecta anomalia via IRF e gera justificativa XAI em linguagem natural."
    ),
    (
        "06 / 07",
        "🤖  Hiper-Automação do COAF",
        "Relatório de Atividade Suspeita (RAS) gerado por RAG agêntico em < 10 segundos."
    ),
    (
        "07 / 07",
        "🟢  Alerta Verde — Hedge Legítimo",
        "O sistema reconhece o perfil do Poupador e elimina atrito no produto sem sacrificar compliance."
    ),
]

# ─── HELPER: draw a rounded-rectangle pill with semi-transparent background ───
def draw_pill(draw, xy, fill, radius=18):
    """Draw a rounded rectangle at (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)

# ─── HELPER: font loader with fallback ────────────────────────────────────────
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ─── DIAGRAM FIX: improve node text contrast ──────────────────────────────────
def fix_diagram_contrast(img):
    """
    For the architecture diagram slide: scan every pixel.
    - Very dark nodes (near black boxes with light text) → push the node fill
      to a readable dark-navy and ensure the text is bright.
    Strategy: paint a high-contrast semi-transparent overlay only on the gray
    rectangle areas so existing text (drawn on top) is clearly legible.
    We do this by boosting contrast globally on the diagram image.
    """
    from PIL import ImageEnhance
    # Boost contrast so faint gray text becomes readable white
    img = ImageEnhance.Contrast(img).enhance(1.8)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = ImageEnhance.Brightness(img).enhance(1.15)
    return img

# ─── MAIN SLIDE COMPOSER ──────────────────────────────────────────────────────
def compose_slide(image_path, slide_index, canvas_size=CANVAS_SIZE, bg_color=BG_COLOR):
    if not os.path.exists(image_path):
        print(f"  ⚠  Image not found: {image_path}")
        return None

    try:
        canvas = Image.new("RGB", canvas_size, bg_color)

        with Image.open(image_path) as src:
            src = src.convert("RGB")

            is_cover   = "cover"    in os.path.basename(image_path).lower()
            is_diagram = "approval" in os.path.basename(image_path).lower()

            # ── Fix diagram contrast before scaling ──
            if is_diagram:
                src = fix_diagram_contrast(src)

            # ── Reserve footer space for caption pill (60 px) ──
            footer_h  = 110
            max_w     = int(canvas_size[0] * 0.96)
            max_h     = canvas_size[1] - footer_h - 20  # leave room on top too

            if is_cover:
                ratio = min(canvas_size[0] / src.width, canvas_size[1] / src.width)
                ratio = min(canvas_size[0] / src.width, canvas_size[1] / src.height)
            else:
                ratio = min(max_w / src.width, max_h / src.height)

            new_w = max(1, int(src.width  * ratio))
            new_h = max(1, int(src.height * ratio))

            resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Center horizontally; push image up slightly to leave footer room
            offset_x = (canvas_size[0] - new_w) // 2
            offset_y = max(8, (canvas_size[1] - footer_h - new_h) // 2)

            canvas.paste(resized, (offset_x, offset_y))

        # ── Gradient footer bar ─────────────────────────────────────────────
        # Draw a subtle gradient strip at the bottom for the caption
        footer_top = canvas_size[1] - footer_h
        overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_ov  = ImageDraw.Draw(overlay)

        # Gradient: transparent → dark navy
        for row in range(footer_h + 30):
            alpha = int(220 * (row / (footer_h + 30)) ** 1.4)
            draw_ov.line(
                [(0, footer_top - 30 + row), (canvas_size[0], footer_top - 30 + row)],
                fill=(14, 17, 23, min(alpha, 230))
            )
        canvas = canvas.convert("RGBA")
        canvas = Image.alpha_composite(canvas, overlay).convert("RGB")

        # ── Text overlay ───────────────────────────────────────────────────
        draw = ImageDraw.Draw(canvas)

        label, headline, subline = SLIDE_META[slide_index]

        font_label    = load_font(FONT_NORMAL, 28)
        font_headline = load_font(FONT_BOLD,   52)
        font_subline  = load_font(FONT_NORMAL, 34)

        # Slide counter pill (top-left)
        pad = 24
        bbox_l = draw.textbbox((0, 0), label, font=font_label)
        lw, lh = bbox_l[2] - bbox_l[0], bbox_l[3] - bbox_l[1]
        pill_x0, pill_y0 = 48, 36
        pill_x1 = pill_x0 + lw + pad * 2
        pill_y1 = pill_y0 + lh + 14

        # Semi-transparent pill via RGBA composite trick
        pill_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_layer)
        pd.rounded_rectangle(
            [pill_x0, pill_y0, pill_x1, pill_y1],
            radius=12,
            fill=(0, 212, 255, 50)
        )
        canvas = Image.alpha_composite(canvas.convert("RGBA"), pill_layer).convert("RGB")
        draw   = ImageDraw.Draw(canvas)

        draw.text((pill_x0 + pad, pill_y0 + 7), label, font=font_label, fill=ACCENT_CYAN)

        # Headline + subline in footer
        cy = footer_top + 8

        # Truncate headline if needed
        draw.text((60, cy), headline, font=font_headline, fill=TEXT_WHITE)
        cy += 62

        # Wrap subline
        wrapped = textwrap.fill(subline, width=90)
        draw.text((62, cy), wrapped, font=font_subline, fill=TEXT_LIGHT)

        # Thin cyan accent line above footer
        line_y = footer_top - 3
        draw.line([(0, line_y), (canvas_size[0], line_y)], fill=ACCENT_CYAN, width=2)

        return canvas

    except Exception as e:
        print(f"  ✖  Error composing slide {slide_index}: {e}")
        import traceback; traceback.print_exc()
        return None


# ─── PDF BUILDER ─────────────────────────────────────────────────────────────
def build_dark_pdf(image_paths, output_pdf_path):
    slides_ok = []
    temp_files = []

    print("🎨  Composing slides with captions and design overlay...")
    for i, path in enumerate(image_paths):
        print(f"   Slide {i+1}: {os.path.basename(path)}")
        slide = compose_slide(path, i)
        if slide:
            temp_png = f"temp_slide_{i}.png"
            slide.save(temp_png, "PNG", compress_level=1)
            temp_files.append(temp_png)
            slides_ok.append(temp_png)

    if not slides_ok:
        print("No slides were generated.")
        return False

    try:
        doc = fitz.open()
        print("📄  Embedding losslessly into PDF via PyMuPDF...")
        for temp_png in slides_ok:
            img_doc   = fitz.open(temp_png)
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            slide_pdf = fitz.open("pdf", pdf_bytes)
            doc.insert_pdf(slide_pdf)
            slide_pdf.close()

        doc.save(output_pdf_path)
        doc.close()
        print(f"✅  PDF saved: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"✖  Error saving PDF: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        print("🧹  Cleaning temporary assets...")
        for tmp in temp_files:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass


# ─── ENTRYPOINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    reports_dir = "reports"

    slides_list = [
        "linkedin_slide_1_cover.png",
        "USDT Transaction Approval-2026-05-15-183841_dark.png",
        "grafico_irf.png",
        "grafico_correlacao.png",
        "streamlit_scanner_red.png",
        "streamlit_scanner_red_coaf.png",
        "streamlit_scanner_green.png",
    ]

    paths      = [os.path.join(reports_dir, name) for name in slides_list]
    output_pdf = os.path.join(reports_dir, "Presentation_Dark.pdf")

    build_dark_pdf(paths, output_pdf)
