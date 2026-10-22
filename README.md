# CS180 Project 4: Image Warping and Mosaicing

Part A is due Tuesday, Oct 27, 2026. Part B is due Tuesday, Nov 10, 2026.
See `code/README.md` for setup and run instructions.

## Part A: Image Warping and Mosaicing

`code/parta.ipynb` estimates homographies from manual correspondences, rectifies
images with nearest-neighbor and bilinear interpolation, and blends warped
photos into mosaics.

## Part B: Feature Matching for Autostitching

`code/partb.ipynb` automatically aligns the same three image pairs using:

1. Harris corner detection with the course's `code/harris.py` and adaptive
   non-maximal suppression (ANMS) to select 500 corners per image.
2. Normalized 8×8 feature descriptors sampled from 40×40 image patches.
3. Nearest-neighbor feature matching with a ratio test.
4. RANSAC to reject outliers and estimate homographies, followed by the Part A
   warping and blending pipeline to create automatic mosaics.

Run `parta.ipynb` first, then `partb.ipynb`, from `code/`. Both notebooks save
results to `code/outputs/`; Part B uses the Part A mosaics for its manual versus
automatic comparisons. Its outputs include corner selections, descriptors,
feature matches, and automatic mosaics.

## Website

The write-up is a Quarto site in `website/`, set up the same way as Project 3.
After the notebook saves its results to `code/outputs/`, rebuild the figures
and preview:

```bash
.venv/bin/python website/scripts/build_figures.py
cd website && quarto preview
```

The figure builder exports the results of both notebooks.

Pushing `website/` to `main` publishes it to GitHub Pages through
`.github/workflows/pages.yml`.
