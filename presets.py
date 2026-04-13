import json
import os

PRESETS_FILE = 'presets.json'

# Default parameter values — "zero state" means no edits applied
DEFAULT_PARAMS = {
    # Light
    "exposure": 0.0,
    "brightness": 1.0,
    "contrast": 1.0,
    "highlights": 0,
    "shadows": 0,
    "whites": 0,
    "blacks": 0,
    # Color
    "temperature": 0,
    "tint": 0,
    "saturation": 1.0,
    "vibrance": 1.0,
    "hue": 0,
    # Effects
    "grain": 0,
    "vignette": 0,
    "glow": 0,
    "fade": 0,
    "clarity": 0,
    "sharpen": 0.0,
    "blur": 0.0,
    "light_leak": 0,
    "sun_flare": 0,
    "noise_reduction": 0,
    "posterize": 0,
    "sepia": 0,
    "motion_blur": 0,
    "ghosting": 0,
    # Shape Blur
    "shape_blur": 0,
    "shape_blur_shape": 0,
    "shape_blur_invert": 1,
    "shape_blur_size": 50,
    "shape_blur_feather": 30,
    "shape_blur_x": 50,
    "shape_blur_y": 50,
}

BUILTIN_PRESETS = {
    "Golden Foliage": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": 0.05,
            "contrast": 1.1,
            "highlights": -15,
            "shadows": 5,
            "blacks": -10,
            "temperature": 30,
            "tint": 5,
            "saturation": 1.12,
            "vibrance": 1.05,
        },
        "builtin": True,
        "cover": "/preset-cover/Golden Hour Glow.jpg",
    },
    "Vintage Glow": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": 0.2,
            "brightness": 1.1,
            "contrast": 0.85,
            "highlights": -10,
            "shadows": 20,
            "whites": 10,
            "blacks": 15,
            "temperature": 25,
            "tint": 5,
            "saturation": 0.85,
            "vibrance": 0.9,
            "grain": 4,
            "glow": 15,
            "fade": 12,
            "clarity": -10,
            "ghosting": 45,
        },
        "builtin": True,
        "cover": "/preset-cover/Golden Film Haze.jpg",
    },
    "Cool Street": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": -0.1,
            "brightness": 0.95,
            "contrast": 1.05,
            "highlights": -15,
            "shadows": 5,
            "whites": -10,
            "blacks": -10,
            "temperature": -20,
            "tint": -10,
            "saturation": 0.85,
            "vibrance": 0.95,
            "grain": 4,
            "clarity": 10,
            "sharpen": 0.3,
        },
        "builtin": True,
        "cover": "/preset-cover/Cinematic Solitude.jpg",
    },
    "Noir Contrast": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": -0.1,
            "brightness": 0.95,
            "contrast": 1.3,
            "highlights": 10,
            "shadows": -15,
            "whites": 15,
            "blacks": -25,
            "saturation": 0.0,
            "vibrance": 0.0,
            "grain": 3,
            "vignette": 5,
            "clarity": 20,
            "sharpen": 0.4,
        },
        "builtin": True,
        "cover": "/preset-cover/Noir Film Portrait.jpg",
    },
    "Rainy Night": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": -0.15,
            "brightness": 0.92,
            "contrast": 1.12,
            "highlights": -10,
            "shadows": 5,
            "blacks": -15,
            "temperature": 15,
            "tint": -5,
            "saturation": 0.9,
            "vibrance": 0.95,
            "vignette": 3,
        },
        "builtin": True,
        "cover": "/preset-cover/Rainy Cinema.jpg",
    },
    "Soft Pastoral": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": 0.15,
            "brightness": 1.1,
            "contrast": 0.9,
            "highlights": -15,
            "shadows": 15,
            "whites": 5,
            "temperature": 20,
            "tint": 5,
            "saturation": 1.05,
            "vibrance": 1.1,
            "glow": 5,
            "clarity": -15,
            "ghosting": 12,
        },
        "builtin": True,
        "cover": "/preset-cover/Golden Petal Dream.jpg",
    },
    "Hazy Riverlight": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": 0.2,
            "brightness": 1.15,
            "contrast": 0.8,
            "highlights": -30,
            "shadows": 20,
            "whites": 15,
            "blacks": 5,
            "temperature": 40,
            "tint": 10,
            "vibrance": 0.9,
            "glow": 10,
            "fade": 5,
            "clarity": -10,
            "sun_flare": 10,
            "ghosting": 25,
        },
        "builtin": True,
        "cover": "/preset-cover/Golden Reverie.jpg",
    },
    "Warm Meadow": {
        "params": {
            **DEFAULT_PARAMS,
            "contrast": 1.05,
            "highlights": -10,
            "shadows": 5,
            "blacks": -5,
            "temperature": 20,
            "saturation": 1.1,
            "vibrance": 1.05,
        },
        "builtin": True,
        "cover": "/preset-cover/Golden Elven Haze.jpg",
    },
    "Noir Motion": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": -0.2,
            "brightness": 0.9,
            "contrast": 1.25,
            "highlights": 5,
            "shadows": -20,
            "whites": 10,
            "blacks": -30,
            "saturation": 0.0,
            "vibrance": 0.0,
            "grain": 5,
            "vignette": 5,
            "clarity": 15,
            "motion_blur": 20,
            "ghosting": 18,
        },
        "builtin": True,
        "cover": "/preset-cover/Noir Motion.jpg",
    },
    "Moody Daisies": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": -0.2,
            "brightness": 0.9,
            "contrast": 1.05,
            "highlights": -10,
            "shadows": 5,
            "whites": -10,
            "blacks": -15,
            "temperature": -15,
            "tint": -10,
            "saturation": 0.8,
            "vibrance": 0.85,
            "vignette": 3,
            "clarity": 10,
            "sharpen": 0.3,
        },
        "builtin": True,
        "cover": "/preset-cover/Twilight Meadow.jpg",
    },
    "Soft Editorial": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": 0.05,
            "brightness": 1.03,
            "contrast": 0.95,
            "highlights": -10,
            "shadows": 8,
            "blacks": 3,
            "temperature": 8,
            "tint": -2,
            "saturation": 1.02,
            "vibrance": 1.05,
            "clarity": 5,
            "sharpen": 0.15,
        },
        "builtin": True,
        "cover": "/preset-cover/Meadow Editorial.jpg",
    },
    "Golden Dusk": {
        "params": {
            **DEFAULT_PARAMS,
            "exposure": -0.2,
            "brightness": 0.9,
            "contrast": 1.1,
            "highlights": -10,
            "shadows": 5,
            "blacks": -15,
            "temperature": 20,
            "tint": -3,
            "saturation": 0.88,
            "vibrance": 0.95,
            "vignette": 3,
        },
        "builtin": True,
        "cover": "/preset-cover/Golden Dusk Cinema.jpg",
    },
}


DELETED_FILE = 'deleted_builtins.json'


def _load_deleted_builtins():
    if os.path.exists(DELETED_FILE):
        with open(DELETED_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def _save_deleted_builtins(deleted):
    with open(DELETED_FILE, 'w') as f:
        json.dump(deleted, f)


def load_presets():
    """Load presets from file, merging with builtins (excluding deleted ones)."""
    deleted = _load_deleted_builtins()
    presets = {k: v for k, v in BUILTIN_PRESETS.items() if k not in deleted}
    if os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, 'r') as f:
            try:
                user_presets = json.load(f)
                presets.update(user_presets)
            except json.JSONDecodeError:
                pass
    return presets


def save_presets(presets):
    """Save only user presets (not builtins) to file."""
    user_presets = {k: v for k, v in presets.items() if not v.get('builtin', False)}
    with open(PRESETS_FILE, 'w') as f:
        json.dump(user_presets, f, indent=2)
