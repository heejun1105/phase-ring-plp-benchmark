# Visualization review and presentation semantics

This is the historical V3/V4 review. Its precision description refers to the
unchanged [earlier two-setting plot](../animations/legacy_two_settings_phase_precision.gif).
The current three-way versions are described in
[conventional_comparison.md](conventional_comparison.md). The current article
keeps all wave-angle content together before photograph denoising; see
[reproduction.md](reproduction.md) for its shorter video edits.

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

The initial gallery used overflow/LUT, architecture and speed race: they expose directly testable arithmetic and actual timing. The denoising and ablation results are supplements, since neither establishes a faithful PLP image algorithm or general quality superiority. The precision animation adds a clear error/efficiency tradeoff.

Each animation has five full-size review frames and a 720x405 README-scale image in `results/visualizations/`. The final GIF itself is decoded and compared with source-rendered frames to detect stale canvases, palette artifacts and frame-composition errors. MP4s are fully decoded; duration, dimensions and frame rate are checked. The global GIF palette is stable, and retained-canvas delta frames reduce hero loading cost without changing numerical data.

The review enlarged profile axis and legend text, corrected a crowded precision legend, chose active race posters, retained image aspect ratio, removed image crop padding and made the shared dark-scene display gain explicit. All six GIFs show actual signal/geometry/image changes, rather than only changing text.

## What the animation clock means

- Architecture: conceptual circuit packages, moving signal samples, activated operations and actual numerical outputs. Equal editorial pacing is not a latency measurement or synthesized die layout.
- Race: four input sizes are shown twice, kernel then full pipeline. Each race has a common linear stretch of measured median durations. Completed counters assume uniform replay and are not live execution traces. Kernel representations differ; a common complex-output cost is separately displayed. Incremental traced allocation excludes existing inputs and untracked memory.
- Overflow/LUT: the three specified cases rotate the actual phase index, reveal binary sum bits, discard the carry and activate the addressed sine-LUT word. The source's one-clock concept is not a fabricated-device measurement.
- Noise (initial version): four-column imagery followed by error maps. The final revision is described below. Full-resolution float outputs determine all metrics; display heatmaps are never individually normalized.
- Precision: the 4-degree window is magnified; white uses the recorded complex64 phase, colored curves use actual floor quantization, orange gaps show actual error. The separate product-RMSE dataset includes two independently quantized inputs.
- Ablation: actual intensities and profiles of clean/V1/V2 outputs, plus full-suite means. Dark images use one common display gain. The moving profile cursor guides the eye and is not a hardware signal trace.

Both prototype variants must retain the label **PLP-Inspired Experimental Prototype - Not a Validated Implementation of the Original PLP Equations** in documentation; the noise animation displays it explicitly. Amber identifies unverified claims/limitations, not measured energy.

## Final refinement review

The original 30 full-size frames and all six 720-pixel posters were reviewed. Architecture, overflow/LUT, NumPy race, precision and edge ablation are preserved byte-for-byte. The old noise demo spent 8 of 12 seconds on heatmaps, with four small image panels; the replacement gives actual images most of the timeline. No denoising algorithm or quality/timing CSV changed.

At that revision the README opened with native C++, then overflow/LUT and architecture. The native race uses a common linear replay of those medians; completion counters assume uniform progress and are editorial, not instrumented execution traces. The giant ratios always name the four-trig baseline. A separate angle-sum/two-trig control is shown before accuracy, making baseline dependence explicit. Input angles and transcendental math are double precision; the output container is complex<float>. This is not a pure FP32 arithmetic throughput claim.

The image-first noise revision uses completed real outputs, identical crop/display conditions per comparison, labeled editorial wipes, clean-reference crops and later common-scale pixel/edge errors. The final full-suite summary exposes both V2 quality losses and time/edge gains. Edge score is custom and not a standard quality metric. See [revision details](noise_visual_revision.md).

Native and revised noise media run 15 seconds; the five retained demos run 12 seconds. Both new sequences blend to their opening frame over the final 0.8 seconds. Validation decodes full MP4 streams, verifies GIF timing/loop metadata, compares decoded GIF pixels against the source renderer and checks first/last-frame continuity. Size optimization uses a shared palette and delta frames rather than individual image enhancement.
