# Setup and reproduction

```bash
python -m venv .venv
# Windows: .venv/Scripts/Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.render_curated_gallery --preview-only
python -m scripts.public_gallery
```

The article is organized by topic: wave-angle calculation, then photograph
denoising. Its nine selected videos each have a different role. Alternate and
earlier versions are listed once in the [media archive](media_archive.md),
without repeated embeds. `scripts/gallery_catalog.py` defines the order.

To regenerate the four shortened article videos, run
`python -m scripts.render_curated_gallery`. It cuts and paces existing scene
functions; it does not rerun the experiments. Timing summaries are shown with
the CPU race, while the precision and wave clips focus on their output changes.
The photo clip and error-map clip cover different parts of the image study.

The other selected GIF/MP4 pairs are retained unchanged. Their renderers and
the full alternative versions can be reproduced with:

```bash
python -m scripts.render_public_visuals
python -m scripts.render_story_variants
python -m scripts.render_conventional_comparisons
python -m scripts.render_curated_gallery
python -m scripts.public_gallery
```

The image diagnostics and ablation use the recorded outputs from
`results/visual_study/`. The source experiment setup is documented in
[visual_study.md](visual_study.md). The separate C++ and NumPy timings have
different execution and allocation policies; see [native_audit.md](native_audit.md)
and [measurements.md](measurements.md).

Article GIFs are 960x540 and MP4s are 1920x1080 at 24 fps. The new edits use
25 fps GIFs and a 0.8-second loop blend. Their cut map, decoded-file checks and
review frames are in [results/curated_gallery](../results/curated_gallery).

```bash
python -m scripts.validate_curated_gallery
python -m scripts.validate_conventional_comparisons
python -m scripts.validate_story_variants
python -m scripts.validate_public_visuals
python -m scripts.validate_reader_update
```

These checks cover selected-video order, duplicate embeds, archive coverage,
decoded GIF/MP4 streams, retained measurement data, the original English paper
and existing numerical model tests. Their records describe software and
presentation checks, not a human comprehension study.
