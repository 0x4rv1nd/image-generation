from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import os
import uuid
import re

app = Flask(__name__)

# Config
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
FONT_PATH = "Roboto-Italic-VariableFont_wdth,wght.ttf"
FONT_SIZE = 60
LINE_SPACING = 20
MARGIN = 100
BACKGROUND_IMAGE = "template.jpg"
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Sanitize filename
def sanitize_filename(text, max_length=40):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:max_length]

# Wrap text for drawing
def wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return [""]
    
    lines = []
    current = words[0]
    
    for word in words[1:]:
        test = f"{current} {word}"
        w, _ = font.getsize(test)
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

@app.route("/", methods=["GET"])
def home():
    return "🖼️ Quote Image Generator is Live!"

@app.route("/generate_quote_image", methods=["POST"])
def generate_quote_image():
    data = request.get_json()
    quote = data.get("quote", "").strip()

    if not quote:
        return jsonify({"error": "No quote provided"}), 400

    try:
        image = Image.open(BACKGROUND_IMAGE).convert("RGB")
        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
    except Exception as e:
        return jsonify({"error": f"Failed to load background image: {str(e)}"}), 500

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    raw_lines = quote.splitlines()
    all_lines = []
    max_text_w = IMAGE_WIDTH - 2 * MARGIN

    for line in raw_lines:
        if line.strip():
            wrapped = wrap_text(line, font, max_text_w)
            all_lines.extend(wrapped)
        else:
            all_lines.append("")

    line_heights = [font.getsize(ln)[1] if ln.strip() else FONT_SIZE for ln in all_lines]
    total_h = sum(line_heights) + LINE_SPACING * (len(all_lines) - 1)
    y = (IMAGE_HEIGHT - total_h) / 2

    for ln, h in zip(all_lines, line_heights):
        if ln.strip():
            w, _ = font.getsize(ln)
            x = (IMAGE_WIDTH - w) / 2
            draw.text((x, y), ln, font=font, fill="white")
        y += h + LINE_SPACING

    # Metadata
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Caption", quote)

    # Filename from quote
    filename_base = sanitize_filename(quote)
    filename = f"{filename_base}.png"
    filepath = os.path.join(STATIC_FOLDER, filename)

    # Ensure uniqueness (optional overwrite protection)
    if os.path.exists(filepath):
        filename = f"{filename_base}_{uuid.uuid4().hex[:6]}.png"
        filepath = os.path.join(STATIC_FOLDER, filename)

    image.save(filepath, format="PNG", pnginfo=meta)

    # Replace with your actual Render domain:
    public_url = f"https://image-generation-sbsi.onrender.com/static/{filename}"
    return jsonify({"image_url": public_url})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
