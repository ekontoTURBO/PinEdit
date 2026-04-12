<p align="center">
  <img src="static/logo.png" alt="Pinedit" width="80" height="80" style="border-radius: 16px;">
</p>

<p align="center">
  <img src="static/logo-text.png" alt="Pinedit" height="36">
</p>

<p align="center">
  <em>Pinterest-aesthetic photo editor with live preview, batch processing, and curated presets.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/flask-3.x-green?style=flat-square" alt="Flask">
  <img src="https://img.shields.io/badge/pillow-11.x-orange?style=flat-square" alt="Pillow">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" alt="License">
</p>

---

## What is Pinedit?

Pinedit is a local photo editor built for content creators who want **consistent, aesthetic color grading** across their photos. Upload one or many photos, pick a preset or tweak sliders, see the result live, and export everything with one click.

No accounts. No cloud. Runs entirely on your machine.

---

## Features

- **Live Preview** -- see edits in real-time as you adjust sliders
- **Batch Processing** -- upload multiple photos, apply the same grade to all, export as ZIP
- **24 Adjustment Sliders** -- exposure, contrast, temperature, saturation, vibrance, clarity, grain, vignette, glow, fade, motion blur, and more
- **Curated Presets** -- 12 built-in presets based on real reference photos, with cover art
- **Custom Presets** -- save your own presets with the current preview as cover art
- **Drag & Drop Upload** -- drop photos directly into the editor
- **Fanned Card Stack** -- browse batch photos in an iPhone-style curved card strip
- **Export Settings** -- choose JPEG, PNG, or WebP format with quality control
- **Custom Export Path** -- pick a folder on your machine via native file explorer
- **One-Click Launch** -- double-click `start.bat` (Windows) or `./start.sh` (Mac/Linux)
- **EXIF-Aware** -- portrait photos from phones stay portrait

---

## Quick Start

### Windows

```
Double-click start.bat
```

### Mac / Linux

```bash
chmod +x start.sh
./start.sh
```

That's it. The launcher will:
1. Create a virtual environment (if needed)
2. Install dependencies
3. Start the app
4. Open your browser at `http://localhost:5000`

---

## Manual Setup

If you prefer to set things up yourself:

```bash
# Clone the repo
git clone https://github.com/your-username/pinedit.git
cd pinedit

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open **http://localhost:5000** in your browser.

---

## How to Use

### 1. Upload

Drag and drop photos into the center area, or click to browse. Single or multiple files.

### 2. Edit

- **Pick a preset** from the left panel -- each has a cover photo showing the vibe
- **Fine-tune with sliders** on the right panel (Light, Color, Effects groups)
- **Double-click** any slider to reset it to default
- The preview updates live as you adjust

### 3. Batch

When multiple photos are uploaded, they appear as a fanned card stack at the bottom. Click any card to preview that photo with current settings. All photos get the same edits on export.

### 4. Export

Click **Export** to download a ZIP with all edited photos at full resolution. Configure format (JPEG/PNG/WebP), quality, and output folder in Settings.

### 5. Save Presets

Click **Save as Preset**, name it, and the current preview becomes the cover art. Your presets appear alongside the built-in ones.

---

## Adjustment Sliders

| Group | Sliders |
|-------|---------|
| **Light** | Exposure, Brightness, Contrast, Highlights, Shadows, Whites, Blacks |
| **Color** | Temperature, Tint, Saturation, Vibrance, Hue |
| **Effects** | Film Grain, Vignette, Soft Glow, Fade, Clarity, Sharpen, Blur, Motion Blur, Light Leak, Sun Flare, Denoise, Posterize, Sepia |

---

## Built-in Presets

| Preset | Vibe |
|--------|------|
| Golden Foliage | Warm amber, rich golden hour |
| Vintage Glow | Dreamy film with soft glow |
| Cool Street | Cool blue-green, muted tones |
| Noir Contrast | Classic high-contrast B&W |
| Rainy Night | Moody amber night cinema |
| Soft Pastoral | Gentle warm pastels |
| Hazy Riverlight | Sun-drenched golden haze |
| Warm Meadow | Vibrant golden greens |
| Noir Motion | Dark dramatic B&W |
| Moody Daisies | Cool teal, dark, atmospheric |
| Soft Editorial | Dreamy, warm, editorial |
| Golden Dusk | Cinematic golden hour silhouette |

---

## Settings

Click the gear icon in the top bar to access:

- **Export Format** -- JPEG, PNG, or WebP
- **Export Quality** -- 50-100 (JPEG/WebP)
- **Export Folder** -- browse for a folder or use browser download

---

## Project Structure

```
pinedit/
├── start.bat              # Windows launcher
├── start.sh               # Mac/Linux launcher
├── requirements.txt       # Python dependencies
├── app.py                 # Flask backend + image processing
├── presets.py             # Preset definitions + load/save
├── presets.json           # User-saved presets
├── settings.json          # User settings
├── static/
│   ├── logo.png           # App icon
│   ├── logo-text.png      # App wordmark
│   ├── style.css          # UI styles
│   └── editor.js          # Frontend logic
├── templates/
│   └── index.html         # Single-page editor
├── preset_covers/         # Preset cover art images
└── uploads/               # Temp export storage
```

---

## Requirements

- Python 3.9+
- Flask
- Pillow

No other dependencies. No Node.js. No build step.

---

<p align="center">
  <img src="static/logo.png" alt="Pinedit" width="24" height="24" style="border-radius: 6px;">
  &nbsp;
  <strong>Pinedit</strong> &mdash; Created by <strong>Cognitra</strong>
</p>
