"""Build WebP assets (PNG for the interpolation close-ups) and Quarto figures from the notebook outputs.

Run from the project root after saving results:
    .venv/bin/python website/scripts/build_figures.py

Keep SETS and RECTIFY in sync with code/parta.ipynb.
"""
from html import escape
from functools import cache
import json
from pathlib import Path
import shutil

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT.parent / "code"
ASSETS = ROOT / "assets"
FIGURES = ROOT / "_figures"
MAX_SIDE = 2000  # Preserve enough detail for wide mosaics.

SETS = {
    # name: (title, scene, [(source photo in code/images/, position, what it shows)], index of the reference photo)
    "set1": ("Set 1", "Visitor Center sign", [
        ("set1_left.jpg", "Left", "road and crosswalk"),
        ("set1_right.jpg", "Right", "sign and olive tree at the corner"),
    ], 1),
    "set2": ("Set 2", "Olive tree path", [
        ("set2_left.jpg", "Left", "path through the olive trees"),
        ("set2_right.jpg", "Right", "olive trees and black louvered building"),
    ], 1),
    "set3": ("Set 3", "Apartment walkway", [
        ("set3_left.jpg", "Left", "left building and walkway"),
        ("set3_right.jpg", "Right", "walkway and right building"),
    ], 1),
}
RECTIFY = {
    # Output stem: (title, source photo in code/images/)
    "rect1": ("Rectification 1: poster frame", "rect1.jpg"),
    "rect2": ("Rectification 2: flyer", "rect2.jpg"),
    "rect3": ("Rectification 3: menu board", "rect3.jpg"),
}

ASSETS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)
manifest = {"assets": []}


@cache
def export_asset(source, name, lossless=False):
    """Convert code/<source> to assets/<name>.webp, or copy it byte for byte as PNG if lossless.

    Returns (published file name, size). Repeated figures reuse the same export.
    """
    path = CODE / source
    if lossless:
        shutil.copyfile(path, ASSETS / f"{name}.png")
        with Image.open(path) as im:
            size = im.size
        manifest["assets"].append({"file": f"{name}.png", "source": source, "size": list(size)})
        return f"{name}.png", size
    with Image.open(path) as original:
        im = ImageOps.exif_transpose(original)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    im.save(ASSETS / f"{name}.webp", quality=88, method=6)
    manifest["assets"].append({"file": f"{name}.webp", "source": source, "size": list(im.size)})
    return f"{name}.webp", im.size


def figure_html(source, name, label, extra="", lossless=False):
    file, (width, height) = export_asset(source, name, lossless)
    body = (f'<a href="assets/{file}" class="lightbox" data-gallery="{name.split("-")[0]}" '
            f'data-glightbox="description: {escape(label, quote=True)}">'
            f'<img src="assets/{file}" width="{width}" height="{height}" '
            f'alt="{escape(label, quote=True)}" loading="lazy" decoding="async"></a>')
    return f'<figure {extra}>{body}<figcaption>{escape(label)}</figcaption></figure>'


def figure_grid(items):
    return (f'<div class="result-grid cols-{len(items)}">\n'
            + '\n'.join(figure_html(*item) for item in items) + '\n</div>\n')


def wide_figure(source, name, label, lossless=False):
    return figure_html(source, name, label, 'class="course-figure"', lossless) + '\n'


def write_figure(name, body):
    (FIGURES / f"{name}.qmd").write_text(body)


for key, (title, scene, photos, ref) in SETS.items():
    sources = [(f"images/{f}", f"{key}-source-{i}",
                f"{position}{' (reference)' if i == ref else ''}: {shows}")
               for i, (f, position, shows) in enumerate(photos)]
    heading = f"\n**{title}: {scene}**\n\n"
    write_figure(f"photos-{key}", heading + figure_grid(sources))
    # One points figure per image matched to the reference.
    write_figure(f"correspondences-{key}", "".join(
        wide_figure(f"outputs/{key}_{i}_points.png", f"{key}-correspondences-{i}",
             f"{title}: numbered correspondences between the {position.lower()} photo and the reference")
        for i, (_, position, _) in enumerate(photos) if i != ref))
    write_figure(f"mosaic-{key}", heading + figure_grid(sources)
          + wide_figure(f"outputs/{key}_mosaic.jpg", f"{key}-mosaic", f"{title} mosaic"))

for key, (title, original) in RECTIFY.items():
    write_figure(f"rectify-{key}", f"\n**{title}**\n\n" + figure_grid([
        (f"images/{original}", f"{key}-original", "Original"),
        (f"outputs/{key}_rectified_nearest.png", f"{key}-nearest", "Rectified · nearest neighbor"),
        (f"outputs/{key}_rectified_bilinear.png", f"{key}-bilinear", "Rectified · bilinear"),
    ]))
    # The notebook saves the same crop from both results side by side. Lossless, so the
    # pixel-level differences between the two methods are not blurred by compression.
    write_figure(f"zoom-{key}", wide_figure(f"outputs/{key}_zoom.png", f"{key}-zoom",
                                            f"{title}: nearest neighbor (left) vs. bilinear (right), zoomed",
                                            lossless=True))

(ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Built {len(list(FIGURES.glob('*.qmd')))} figure layouts with {len(manifest['assets'])} assets.")
