from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from presets import load_presets, save_presets, DEFAULT_PARAMS, _load_deleted_builtins, _save_deleted_builtins
from zipfile import ZipFile
from PIL import Image, ImageEnhance, ImageFilter, ImageChops, ImageDraw, ImageOps
import io
import os
import base64
import json
import random
import math

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PRESET_COVERS_FOLDER = 'preset_covers'
SETTINGS_FILE = 'settings.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

for folder in [UPLOAD_FOLDER, PRESET_COVERS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ─── Settings ────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "export_path": "",  # empty = browser download
    "export_format": "jpg",
    "export_quality": 95,
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                saved = json.load(f)
                return {**DEFAULT_SETTINGS, **saved}
            except json.JSONDecodeError:
                pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# ─── Image Processing Engine ────────────────────────────────────────────────

def apply_exposure(img, value):
    """Exposure: multiplicative brightness. value in [-2, 2], 0 = no change."""
    if value == 0:
        return img
    factor = 2 ** value  # EV-style: +1 = 2x bright, -1 = 0.5x
    return img.point(lambda x: min(255, max(0, int(x * factor))))


def apply_brightness(img, value):
    """Brightness via ImageEnhance. value in [0.5, 2.0], 1.0 = no change."""
    if value == 1.0:
        return img
    return ImageEnhance.Brightness(img).enhance(value)


def apply_contrast(img, value):
    """Contrast via ImageEnhance. value in [0.5, 2.0], 1.0 = no change."""
    if value == 1.0:
        return img
    return ImageEnhance.Contrast(img).enhance(value)


def apply_highlights(img, value):
    """Adjust bright pixels. value in [-100, 100], 0 = no change."""
    if value == 0:
        return img
    factor = value / 100.0
    def adjust(x):
        if x > 128:
            shift = factor * (x - 128) / 127.0 * 50
            return min(255, max(0, int(x + shift)))
        return x
    return img.point(adjust)


def apply_shadows(img, value):
    """Adjust dark pixels. value in [-100, 100], 0 = no change."""
    if value == 0:
        return img
    factor = value / 100.0
    def adjust(x):
        if x < 128:
            shift = factor * (128 - x) / 128.0 * 50
            return min(255, max(0, int(x + shift)))
        return x
    return img.point(adjust)


def apply_whites(img, value):
    """Adjust the white point. value in [-100, 100], 0 = no change."""
    if value == 0:
        return img
    factor = value / 100.0
    def adjust(x):
        if x > 200:
            shift = factor * 30
            return min(255, max(0, int(x + shift)))
        return x
    return img.point(adjust)


def apply_blacks(img, value):
    """Adjust the black point. value in [-100, 100], 0 = no change."""
    if value == 0:
        return img
    factor = value / 100.0
    def adjust(x):
        if x < 55:
            shift = factor * 30
            return min(255, max(0, int(x + shift)))
        return x
    return img.point(adjust)


def apply_temperature(img, value):
    """Color temperature. value in [-100, 100], 0 = no change. Positive = warm, negative = cool."""
    if value == 0:
        return img
    r, g, b = img.split()
    factor = value / 100.0
    r = r.point(lambda x: min(255, max(0, int(x + factor * 25))))
    b = b.point(lambda x: min(255, max(0, int(x - factor * 25))))
    return Image.merge('RGB', (r, g, b))


def apply_tint(img, value):
    """Green/Magenta tint. value in [-100, 100], 0 = no change."""
    if value == 0:
        return img
    r, g, b = img.split()
    factor = value / 100.0
    g = g.point(lambda x: min(255, max(0, int(x + factor * 20))))
    return Image.merge('RGB', (r, g, b))


def apply_saturation(img, value):
    """Saturation via ImageEnhance. value in [0.0, 2.0], 1.0 = no change."""
    if value == 1.0:
        return img
    return ImageEnhance.Color(img).enhance(value)


def apply_vibrance(img, value):
    """Selective saturation — boosts muted colors more than saturated ones.
    value in [0.0, 2.0], 1.0 = no change."""
    if value == 1.0:
        return img
    import colorsys
    pixels = img.load()
    w, h = img.size
    result = img.copy()
    res_pixels = result.load()
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            h_val, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            # Boost less saturated colors more
            boost = (1.0 - s) * (value - 1.0)
            new_s = min(1.0, max(0.0, s + boost * s))
            nr, ng, nb = colorsys.hsv_to_rgb(h_val, new_s, v)
            res_pixels[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255))
    return result


def apply_vibrance_fast(img, value):
    """Fast vibrance approximation using saturation with reduced effect on already-saturated areas.
    Used for preview speed. value in [0.0, 2.0], 1.0 = no change."""
    if value == 1.0:
        return img
    # Blend between original and saturated version based on how much change is needed
    saturated = ImageEnhance.Color(img).enhance(value)
    # Use a moderate blend to approximate selective saturation
    blend_factor = min(1.0, abs(value - 1.0))
    if value > 1.0:
        return Image.blend(img, saturated, blend_factor * 0.7)
    else:
        return Image.blend(img, saturated, blend_factor)


def apply_hue(img, value):
    """Hue rotation. value in [-180, 180] degrees, 0 = no change."""
    if value == 0:
        return img
    hsv = img.convert('HSV')
    h, s, v = hsv.split()
    shift = int(value / 360.0 * 256) % 256
    h = h.point(lambda x: (x + shift) % 256)
    return Image.merge('HSV', (h, s, v)).convert('RGB')


def apply_grain(img, value):
    """Film grain overlay. value in [0, 100], 0 = no grain."""
    if value == 0:
        return img
    strength = value * 0.5  # scale to reasonable noise level
    w, h = img.size
    noise = Image.effect_noise((w, h), strength)
    noise_rgb = Image.merge('RGB', (noise, noise, noise))
    return ImageChops.add(img, noise_rgb, scale=2.0)


def apply_vignette(img, value):
    """Radial vignette. value in [0, 100], 0 = no vignette."""
    if value == 0:
        return img
    w, h = img.size
    mask = Image.new('L', (w, h), 255)
    draw = ImageDraw.Draw(mask)

    cx, cy = w // 2, h // 2
    max_radius = math.sqrt(cx * cx + cy * cy)
    intensity = value / 100.0

    steps = 40
    for i in range(steps):
        t = i / steps
        radius_factor = 1.0 - t * 0.6 * intensity
        brightness = int(255 * (1.0 - t * t * intensity * 0.8))
        rx = int(cx * radius_factor * 2)
        ry = int(cy * radius_factor * 2)
        draw.ellipse(
            [cx - rx, cy - ry, cx + rx, cy + ry],
            fill=brightness
        )

    # Apply the vignette mask
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(w, h) // 6))
    result = img.copy()
    black = Image.new('RGB', (w, h), (0, 0, 0))
    result = Image.composite(result, black, mask)
    return result


def apply_glow(img, value):
    """Soft glow/bloom. value in [0, 100], 0 = no glow."""
    if value == 0:
        return img
    strength = value / 100.0 * 0.6
    radius = max(5, int(value / 100.0 * 20))
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    return Image.blend(img, blurred, strength)


def apply_fade(img, value):
    """Fade/matte effect — lifts blacks and desaturates. value in [0, 100], 0 = no fade."""
    if value == 0:
        return img
    factor = value / 100.0
    # Lift blacks
    lift = int(factor * 40)
    img = img.point(lambda x: min(255, x + lift))
    # Desaturate slightly
    desat = 1.0 - factor * 0.3
    img = ImageEnhance.Color(img).enhance(desat)
    return img


def apply_clarity(img, value):
    """Clarity/micro-contrast via unsharp mask at large radius. value in [-100, 100], 0 = no change."""
    if value == 0:
        return img
    factor = value / 100.0
    if factor > 0:
        # Positive clarity: large-radius unsharp mask for local contrast
        amount = int(factor * 40)  # max 40% at value=100
        return img.filter(ImageFilter.UnsharpMask(radius=20, percent=amount, threshold=3))
    else:
        # Negative clarity: blend toward blurred version for softness
        blurred = img.filter(ImageFilter.GaussianBlur(radius=8))
        return Image.blend(img, blurred, abs(factor) * 0.3)


def apply_sharpen(img, value):
    """Sharpen via UnsharpMask. value in [0, 3.0], 0 = no sharpening."""
    if value == 0:
        return img
    percent = int(value * 100)
    return img.filter(ImageFilter.UnsharpMask(radius=2, percent=percent, threshold=3))


def apply_blur(img, value):
    """Gaussian blur. value in [0, 20], 0 = no blur."""
    if value == 0:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=value))


def apply_motion_blur(img, value):
    """Directional motion blur (horizontal streaks). value in [0, 100], 0 = no effect."""
    if value == 0:
        return img
    distance = max(2, int(value / 4))  # map 0-100 to 0-25px of shift
    result = img
    for i in range(1, distance + 1):
        weight = 0.4 / distance
        shifted_r = ImageChops.offset(img, i, 0)
        shifted_l = ImageChops.offset(img, -i, 0)
        result = Image.blend(result, shifted_r, weight)
        result = Image.blend(result, shifted_l, weight)
    return result


def apply_light_leak(img, value):
    """Warm light leak overlay. value in [0, 100], 0 = no effect."""
    if value == 0:
        return img
    w, h = img.size
    leak = Image.new('RGB', (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(leak)
    # Warm glow from top-left corner
    for i in range(min(w, h)):
        alpha = max(0, 255 - i)
        draw.ellipse(
            [-w // 4 - i, -h // 4 - i, w // 3 + i, h // 3 + i],
            fill=(255, 120, 60)
        )
    leak = leak.filter(ImageFilter.GaussianBlur(radius=max(w, h) // 4))
    alpha = value / 100.0 * 0.25
    return Image.blend(img, leak, alpha)


def apply_sun_flare(img, value):
    """Sun flare effect. value in [0, 100], 0 = no effect."""
    if value == 0:
        return img
    w, h = img.size
    overlay = Image.new('RGB', (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(min(w, h) // 2):
        draw.ellipse(
            [w // 3 - i, -h // 6 - i, w // 3 * 2 + i, h // 3 + i],
            fill=(255, 210, 160)
        )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(w, h) // 5))
    alpha = value / 100.0 * 0.2
    return Image.blend(img, overlay, alpha)


def apply_noise_reduction(img, value):
    """Noise reduction via median filter. value in [0, 10], 0 = no reduction."""
    if value == 0:
        return img
    size = max(3, int(value) * 2 + 1)  # must be odd
    if size % 2 == 0:
        size += 1
    return img.filter(ImageFilter.MedianFilter(size=min(size, 11)))


def apply_posterize(img, value):
    """Posterize effect. value in [0, 100], 0 = no effect (full 8-bit)."""
    if value == 0:
        return img
    # Map 0-100 to 8-2 bits
    bits = max(2, 8 - int(value / 100.0 * 6))
    return ImageOps.posterize(img, bits)


def apply_sepia(img, value):
    """Sepia tone. value in [0, 100], 0 = no effect."""
    if value == 0:
        return img
    gray = ImageOps.grayscale(img)
    sepia = Image.merge('RGB', (
        gray.point(lambda x: min(255, int(x * 1.2))),
        gray.point(lambda x: min(255, int(x * 1.0))),
        gray.point(lambda x: min(255, int(x * 0.8))),
    ))
    factor = value / 100.0
    return Image.blend(img, sepia, factor)


# ─── Edit Pipeline ──────────────────────────────────────────────────────────

# Processing order matters — this is a standard photo editing pipeline
EDIT_PIPELINE = [
    ('exposure', apply_exposure),
    ('brightness', apply_brightness),
    ('contrast', apply_contrast),
    ('highlights', apply_highlights),
    ('shadows', apply_shadows),
    ('whites', apply_whites),
    ('blacks', apply_blacks),
    ('temperature', apply_temperature),
    ('tint', apply_tint),
    ('saturation', apply_saturation),
    ('vibrance', apply_vibrance_fast),
    ('hue', apply_hue),
    ('clarity', apply_clarity),
    ('sharpen', apply_sharpen),
    ('blur', apply_blur),
    ('noise_reduction', apply_noise_reduction),
    ('grain', apply_grain),
    ('vignette', apply_vignette),
    ('glow', apply_glow),
    ('fade', apply_fade),
    ('light_leak', apply_light_leak),
    ('sun_flare', apply_sun_flare),
    ('posterize', apply_posterize),
    ('sepia', apply_sepia),
    ('motion_blur', apply_motion_blur),
]


def edit_image(image, params):
    """Apply all edits in pipeline order."""
    for param_name, func in EDIT_PIPELINE:
        value = params.get(param_name, DEFAULT_PARAMS.get(param_name, 0))
        # Convert to appropriate type
        if isinstance(DEFAULT_PARAMS.get(param_name, 0), float):
            value = float(value)
        else:
            value = int(float(value))
        image = func(image, value)
    return image


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    presets = load_presets()
    return render_template('index.html', presets=presets)


@app.route('/preview', methods=['POST'])
def preview():
    """Live preview endpoint. Receives image + params, returns edited thumbnail as base64."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image'}), 400

    file = request.files['image']
    img = Image.open(io.BytesIO(file.read()))
    img = ImageOps.exif_transpose(img)  # Fix phone portrait rotation
    img = img.convert('RGB')

    # Downscale for fast preview
    max_dim = 800
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # Parse params from form
    params = {}
    for key in DEFAULT_PARAMS:
        if key in request.form:
            params[key] = float(request.form[key])
        else:
            params[key] = DEFAULT_PARAMS[key]

    # Apply edits
    result = edit_image(img, params)

    # Encode to base64 JPEG
    buffer = io.BytesIO()
    result.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode('utf-8')

    return jsonify({'image': f'data:image/jpeg;base64,{b64}'})


@app.route('/export', methods=['POST'])
def export():
    """Export full-resolution edited images as ZIP."""
    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No images'}), 400

    params = {}
    for key in DEFAULT_PARAMS:
        if key in request.form:
            params[key] = float(request.form[key])
        else:
            params[key] = DEFAULT_PARAMS[key]

    settings = load_settings()
    fmt = settings.get('export_format', 'jpg').upper()
    if fmt == 'JPG':
        fmt = 'JPEG'
    quality = settings.get('export_quality', 95)
    ext = 'jpg' if fmt == 'JPEG' else fmt.lower()
    export_path = settings.get('export_path', '').strip()

    zip_name = 'pinedit_export.zip'

    # Determine where to write the zip
    if export_path and os.path.isdir(export_path):
        zip_path = os.path.join(export_path, zip_name)
    else:
        zip_path = os.path.join(UPLOAD_FOLDER, zip_name)

    with ZipFile(zip_path, 'w') as zipf:
        for file in files:
            if file and file.filename:
                img = Image.open(io.BytesIO(file.read()))
                img = ImageOps.exif_transpose(img)
                img = img.convert('RGB')
                result = edit_image(img, params)
                buf = io.BytesIO()
                save_kwargs = {'format': fmt}
                if fmt in ('JPEG', 'WEBP'):
                    save_kwargs['quality'] = quality
                result.save(buf, **save_kwargs)
                buf.seek(0)
                base_name = os.path.splitext(file.filename)[0]
                zipf.writestr(f'pinedit_{base_name}.{ext}', buf.read())

    # If custom path, also send as download
    return send_file(zip_path, as_attachment=True, download_name=zip_name)


@app.route('/save-preset', methods=['POST'])
def save_preset():
    """Save current params as a named preset with optional cover art."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name required'}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400

    params = {}
    for key in DEFAULT_PARAMS:
        if key in data.get('params', {}):
            params[key] = float(data['params'][key])
        else:
            params[key] = DEFAULT_PARAMS[key]

    presets = load_presets()
    presets[name] = {
        'params': params,
        'cover': data.get('cover', None)
    }

    # Save cover art if provided
    if data.get('cover'):
        cover_data = data['cover']
        if cover_data.startswith('data:image'):
            cover_data = cover_data.split(',')[1]
        cover_bytes = base64.b64decode(cover_data)
        cover_path = os.path.join(PRESET_COVERS_FOLDER, f'{name}.jpg')
        with open(cover_path, 'wb') as f:
            f.write(cover_bytes)
        presets[name]['cover'] = f'/preset-cover/{name}.jpg'

    save_presets(presets)
    return jsonify({'success': True, 'presets': presets})


@app.route('/delete-preset/<name>', methods=['DELETE'])
def delete_preset(name):
    """Delete any preset (builtin or custom)."""
    presets = load_presets()
    if name in presets:
        is_builtin = presets[name].get('builtin', False)
        del presets[name]

        if is_builtin:
            # Track deleted builtins so they don't reappear on reload
            deleted = _load_deleted_builtins()
            deleted.append(name)
            _save_deleted_builtins(deleted)
        else:
            save_presets(presets)

        # Remove cover art
        cover_path = os.path.join(PRESET_COVERS_FOLDER, f'{name}.jpg')
        if os.path.exists(cover_path):
            os.remove(cover_path)

    # Return current state
    return jsonify({'success': True, 'presets': load_presets()})


@app.route('/presets', methods=['GET'])
def get_presets():
    return jsonify(load_presets())


@app.route('/preset-cover/<filename>')
def preset_cover(filename):
    return send_from_directory(PRESET_COVERS_FOLDER, filename)


@app.route('/settings', methods=['GET'])
def get_settings():
    return jsonify(load_settings())


@app.route('/settings', methods=['POST'])
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    settings = load_settings()
    settings.update(data)
    save_settings(settings)
    return jsonify(settings)


@app.route('/browse-folder', methods=['POST'])
def browse_folder():
    """Open a native folder picker dialog and return the selected path."""
    import subprocess
    import sys
    import platform

    selected = None
    if platform.system() == 'Windows':
        # Use PowerShell to show folder picker
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$f.Description = 'Select export folder'; "
            "$f.ShowNewFolderButton = $true; "
            "if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath } else { '' }"
        )
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True, text=True, timeout=60
        )
        selected = result.stdout.strip()
    elif platform.system() == 'Darwin':
        # macOS: use osascript
        result = subprocess.run(
            ['osascript', '-e', 'POSIX path of (choose folder with prompt "Select export folder")'],
            capture_output=True, text=True, timeout=60
        )
        selected = result.stdout.strip()
    else:
        # Linux: try zenity
        try:
            result = subprocess.run(
                ['zenity', '--file-selection', '--directory', '--title=Select export folder'],
                capture_output=True, text=True, timeout=60
            )
            selected = result.stdout.strip()
        except FileNotFoundError:
            return jsonify({'error': 'No folder picker available'}), 500

    if selected and os.path.isdir(selected):
        return jsonify({'path': selected})
    return jsonify({'path': ''})


if __name__ == '__main__':
    app.run(debug=False, port=5000)
