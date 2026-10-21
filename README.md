# CS180 Project 4: Image Warping and Mosaicing

Part A is due Tuesday, Oct 27, 2026. Part B is due Tuesday, Nov 10, 2026.
See `code/README.md` for setup and run instructions.

## Website

The write-up is a Quarto site in `website/`, set up the same way as Project 3.
After the notebook saves its results to `code/outputs/`, rebuild the figures
and preview:

```bash
.venv/bin/python website/scripts/build_figures.py
cd website && quarto preview
```

Pushing `website/` to `main` publishes it to GitHub Pages through
`.github/workflows/pages.yml`.
