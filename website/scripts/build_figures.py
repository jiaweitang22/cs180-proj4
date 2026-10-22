"""Copy the notebook outputs into assets/ byte for byte and build the Quarto figures.

Run from the project root after saving results:
    .venv/bin/python website/scripts/build_figures.py

Keep SETS and RECTIFY in sync with code/parta.ipynb; Part B figures come from code/partb.ipynb.
"""
from html import escape
from functools import cache
import json
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT.parent / "code"
ASSETS = ROOT / "assets"
FIGURES = ROOT / "_figures"

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
def export_asset(source, name):
    """Copy code/<source> to assets/<name> unchanged (no resizing or re-encoding), keeping its extension.

    Returns (published file name, size). Repeated figures reuse the same export.
    """
    path = CODE / source
    file = f"{name}{path.suffix}"
    shutil.copyfile(path, ASSETS / file)
    with Image.open(path) as im:
        size = im.size
    manifest["assets"].append({"file": file, "source": source, "size": list(size)})
    return file, size


def figure_html(source, name, label, extra=""):
    file, (width, height) = export_asset(source, name)
    body = (f'<a href="assets/{file}" class="lightbox" data-gallery="{name.split("-")[0]}" '
            f'data-glightbox="description: {escape(label, quote=True)}">'
            f'<img src="assets/{file}" width="{width}" height="{height}" '
            f'alt="{escape(label, quote=True)}" loading="lazy" decoding="async"></a>')
    return f'<figure {extra}>{body}<figcaption>{escape(label)}</figcaption></figure>'


def figure_grid(items):
    return (f'<div class="result-grid cols-{len(items)}">\n'
            + '\n'.join(figure_html(*item) for item in items) + '\n</div>\n')


def wide_figure(source, name, label):
    return figure_html(source, name, label, 'class="course-figure"') + '\n'


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
          + wide_figure(f"outputs/{key}_mosaic.png", f"{key}-mosaic", f"{title} mosaic"))

for key, (title, original) in RECTIFY.items():
    write_figure(f"rectify-{key}", f"\n**{title}**\n\n" + figure_grid([
        (f"images/{original}", f"{key}-original", "Original"),
        (f"outputs/{key}_rectified_nearest.png", f"{key}-nearest", "Rectified · nearest neighbor"),
        (f"outputs/{key}_rectified_bilinear.png", f"{key}-bilinear", "Rectified · bilinear"),
    ]))
    # The notebook saves the same crop from both results side by side.
    write_figure(f"zoom-{key}", wide_figure(f"outputs/{key}_zoom.png", f"{key}-zoom",
                                            f"{title}: nearest neighbor (left) vs. bilinear (right), zoomed"))

# Part B (code/partb.ipynb): same sets; corners and descriptors are shown for Set 1 only.
for key, (title, *_) in SETS.items():
    write_figure(f"matches-{key}", wide_figure(
        f"outputs/{key}_3_matches.png", f"{key}-matches",
        f"{title}: matches that pass the ratio test, left photo to reference"))
    write_figure(f"auto-mosaic-{key}", f"\n**{title}**\n\n" + figure_grid([
        (f"outputs/{key}_mosaic.png", f"{key}-mosaic", f"{title} · manual (Part A)"),
        (f"outputs/{key}_4_mosaic_auto.png", f"{key}-mosaic-auto", f"{title} · automatic (RANSAC)"),
    ]))
write_figure("harris-set1", wide_figure(
    "outputs/set1_1_harris.png", "set1-harris",
    "Set 1, left photo: all Harris corners, the 500 strongest, and the 500 chosen by ANMS"))
write_figure("descriptors-set1", wide_figure(
    "outputs/set1_2_descriptors.png", "set1-descriptors",
    "Set 1: 40×40 windows around eight ANMS corners (top) and their normalized 8×8 descriptors (bottom)"))

(ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Built {len(list(FIGURES.glob('*.qmd')))} figure layouts with {len(manifest['assets'])} assets.")
