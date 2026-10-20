# Visualization review and presentation semantics

Scores below are subjective author self-assessment out of 10 after full-size and 720-pixel-wide review, not an independent user study or scientific measurement. No visual score is used as evidence of computational superiority.

| Demo | Visual Impact | Clarity | Technical Accuracy | Readability | Scientific Credibility | Presentation Quality |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Architecture | 8 | 8 | 9 | 8 | 9 | 8 |
| CPU speed race | 8 | 9 | 9 | 9 | 10 | 9 |
| Overflow and LUT | 9 | 9 | 10 | 9 | 10 | 9 |
| Noise and error maps | 8 | 8 | 9 | 8 | 10 | 8 |
| Quantization and precision | 8 | 9 | 10 | 9 | 10 | 9 |
| Edge / latency ablation | 7 | 8 | 9 | 8 | 10 | 8 |

## Selection and corrections

Overflow/LUT, architecture and speed race lead the README: they expose directly testable arithmetic and actual timing. The denoising and ablation results are supplements, since neither establishes a faithful PLP image algorithm or general quality superiority. The precision animation adds a clear error/efficiency tradeoff.

Each animation has five full-size review frames and a 720x405 README-scale image in `results/visualizations/`. The final GIF itself is decoded and compared with source-rendered frames to detect stale canvases, palette artifacts and frame-composition errors. MP4s are fully decoded; duration, dimensions and frame rate are checked. The global GIF palette is stable, and retained-canvas delta frames reduce hero loading cost without changing numerical data.

The review enlarged profile axis and legend text, corrected a crowded precision legend, chose active race posters, retained image aspect ratio, removed image crop padding and made the shared dark-scene display gain explicit. All six GIFs show actual signal/geometry/image changes, rather than only changing text.

## What the animation clock means

- Architecture: conceptual circuit packages, moving signal samples, activated operations and actual numerical outputs. Equal editorial pacing is not a latency measurement or synthesized die layout.
- Race: four input sizes are shown twice, kernel then full pipeline. Each race has a common linear stretch of measured median durations. Completed counters assume uniform replay and are not live execution traces. Kernel representations differ; a common complex-output cost is separately displayed. Incremental traced allocation excludes existing inputs and untracked memory.
- Overflow/LUT: the three specified cases rotate the actual phase index, reveal binary sum bits, discard the carry and activate the addressed sine-LUT word. The source's one-clock concept is not a fabricated-device measurement.
- Noise: one predeclared case, synchronized crop/zoom, fixed intensity range and shared error scales. The scan line is editorial. Full-resolution float outputs determine all metrics; display heatmaps are never individually normalized.
- Precision: the 4-degree window is magnified; white uses the recorded complex64 phase, colored curves use actual floor quantization, orange gaps show actual error. The separate product-RMSE dataset includes two independently quantized inputs.
- Ablation: actual intensities and profiles of clean/V1/V2 outputs, plus full-suite means. Dark images use one common display gain. The moving profile cursor guides the eye and is not a hardware signal trace.

Both prototype variants must retain the label **PLP-Inspired Experimental Prototype - Not a Validated Implementation of the Original PLP Equations** in documentation; the noise animation displays it explicitly. Amber identifies unverified claims/limitations, not measured energy.
