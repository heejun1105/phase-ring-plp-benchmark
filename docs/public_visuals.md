# Public visual edition: motion before explanation

This visual edition changed presentation, not the experiment. Its original
validation record checked prior files against commit
`b6fffe6484b35a5f54d4a7df13e7474627727742`. The later source/reading update adds
the English paper and revises prose, source metadata and validators. Numerical
algorithms, measured CSVs and recorded image arrays remain unchanged. The
current precision video adds a conventional FP32 panel beside both lookup
settings; its unchanged earlier video is retained as
`legacy_two_settings_public_precision`. [Current comparison methods and archives](conventional_comparison.md).
The three arithmetic demos explain the shortcut, its precision cost
and its correctness; they are optional after the speed and photo comparisons.
[Short reading guide](understanding_the_demos.md). The backup branch is
`backup/pre-public-visuals-b6fffe6`. New artifacts use new filenames and a separate
`results/public_visuals/` directory.

## Five standalone stories

| Story | Duration | Main visible change | Evidence |
| --- | ---: | --- | --- |
| A: Public CPU workflow | 16 s | Waiting tile queues drain; finished queues fill; devices stop at measured completion | Retained native audit medians |
| B: Public phase computing | 14 s | Four real products/combinations versus combining phase hands and a selected LUT word | Shared raw angles; actual quantizer and Q15 output |
| C: Public precision | 15 s | Equal panels show conventional FP32 and both Q15 outputs for one input | Actual reconstructed channels; retained native time and product RMSE |
| D: Bits to LUT | 18 s | LSB-first addition, carry discard, moving retained address, selected signed-Q15 word | Python reference and adapted scalar-sine RTL |
| Photo noise supplement | 18 s | Large same-photo editorial slider, shared detail crops, then real quality/time | Committed camera/fixture outputs and 54-case CSV |

All masters are 1920×1080, H.264/yuv420p at 24 fps, without audio. Standalone
GIFs are 960×540, nominal 25 fps (40 ms per frame), with a shared 256-color
palette and delta-frame compression. The bit/LUT and overview GIFs reserve eight
theme colors so the upper carry and warnings retain their semantic amber.
Encoders may merge identical frames while
retaining duration. Each final 0.8 seconds blends to the opening frame. The new
renderer writes only new edition filenames.

## What the moving objects mean

### A: Work queues

There are 200 drawn tiles per lane, each representing 50,000 phase products.
Input and output tile counts follow a uniform replay of the measured median,
with one common elapsed-time scale for all three lanes in each race. The first
replay compares the four-trig product with Z1024 and Z2048; the second uses the
optimized angle-sum baseline. Queue tiles and moving packets are conceptual
data illustrations, not recorded per-item traces, real CPU queues, instruction
counts or a PIM device. Activity graphics inside processors do not describe
hardware circuitry. Counter completion assumes uniform work and is not an
instrumented property of the measured loops.

The stored medians are 330.3962, 195.6071, 36.9522 and 33.2588 ms. The ratios
8.94x/9.93x use the four-trig baseline; 5.29x/5.88x use the optimized baseline.
All values come from one retained run. The separately recorded repeat changes
timings and reverses the Z1024/Z2048 ranking. This edition collects no new
benchmark results. Same input/output types do not mean the Q15 approximation
has the same accuracy. [Full conditions and compiler/cache audit](native_audit.md).

### B: Arithmetic routes

One concrete pair of raw angles is shared between the conventional complex64
path and the ring path. Quarter-bin offsets expose actual quantization error;
they are not fabricated output perturbations. In Z1024 the input indices are
750 and 400, their sum wraps to 126, and the paired Q15 word is (23452,22883).
The four real products feed the correct subtraction/addition. On the right,
the input hands keep their input phases while the accumulator moves through
phase addition into the selected LUT address. Final waves have equal display
scales and a common carrier clock. Their true angular gap is approximately
0.1762 degrees and is stated without visually exaggerating it.

Both branches use equal editorial stage pacing, which does not encode measured
latency or a synthesized circuit's cycle count. The finite phase identity
applies to unit-magnitude phasors, not arbitrary complex MACs.

### C: Precision

Three equal panels use the same magnified 0–2.109375-degree window. The blue
panel shows conventional FP32 sine/cosine reconstruction without angle bins.
The other two show actual Q15 outputs after floor quantization, using bins of
0.3515625 and 0.17578125 degrees. The orange region and the displayed gaps come
from each reconstructed output phase. FP32 rounding is retained and reported
numerically even when it is smaller than a display pixel.

The final cards give retained median CPU time and angular RMSE for all three
methods, using the optimized summed-angle control. RMSE comes from the first
200,000 input pairs of the 10M native audit, not the animated single-input
trajectory. The two-input 0.29° + 0.29° example appears in the separate target
and wave comparisons. [Current methods, exact values and archives](conventional_comparison.md).

### D: Bits and logical memory

The full-adder trace is computed from each actual operand bit and carry-in.
It shows 1023+1→0 in 10 bits, 750+400→126 in 10 bits and 1500+800→252 in 11
bits. Only the upper carry is discarded; retained bits form the actual LUT
address. A 64-word labeled address window is a logical diagram, not an SRAM
floorplan. The data word travels from the addressed cell to the output.

The RTL stores scalar signed-Q15 sine; the paired cosine and complex64 output
are explicitly labeled software extensions. The addressed sine values are
0, 22883, 22883; cosine values are 32767, 23452, 23452. The ripple presentation
is educational, not a claim that the source RTL contains this exact adder
topology, takes one drawn step per clock, or has measured physical delays.

### Photo supplement

The first six seconds show the entire 512×512 camera photograph enlarged to
700×700 in each of two panels. The left noisy image is fixed; the right reveals
completed Bilateral, V1 and V2 outputs for two seconds each, with a labeled
editorial drag boundary. A clean-reference thumbnail uses the same grayscale
mapping. This is not iterative processing, convergence or live execution.

The next six seconds inspect small text, fine lines, geometry and dark texture
from their own recorded fixtures. These are labeled content changes, not
regions falsely attributed to the camera photograph. Crops and magnification
match across noisy, clean and filtered versions. Only dark texture uses a
shared gain of 1/0.22 with clipping; metrics always use full unscaled arrays.
No method receives sharpening, local contrast enhancement or independent
normalization. Actual-image comparisons precede metrics, with no heatmap
dominating the story. The final six seconds disclose photo-specific and
full-54-case PSNR, SSIM and CPU time for all three filters.

Both variants remain **PLP-Inspired Experimental Prototype — Not a Validated
Implementation of the Original PLP Equations**. V2's lower time than V1 comes
with lower mean PSNR and SSIM. Bilateral is not hidden or declared universally
inferior. [Full image study and custom edge metric](visual_study.md).

## 40-second overview and 12-second preview

| Full MP4 | Chapter |
| --- | --- |
| 0–3 s | Same task. Different computing approach. |
| 3–13 s | Work queues and both native CPU baselines |
| 13–22 s | Conventional route versus phase addition and lookup |
| 22–31 s | Quantization steps and recorded precision |
| 31–38 s | First 10-bit carry/register/LUT example |
| 38–40 s | Project title and evidence-oriented closing |

Short chapter crossfades and changed excerpt pacing are editorial. The overview
does not preserve the standalone videos' wall-clock playback length; neither
timeline is an actual CPU duration. The README GIF is a distinct 12-second
edit (four seconds of A, three of B, three of C, two of D), not the entire
40-second video. Its last 0.8 seconds blends to its opening frame.

## Reproduce and assess

```bash
python -m scripts.render_public_visuals --preview-only
python -m scripts.render_public_visuals
python -m scripts.render_conventional_comparisons
python -m scripts.public_gallery
python -m scripts.validate_public_visuals
```

Use `--only <name>` to render one new animation. The five standalone filenames
are `public_cpu_workflow`, `public_phase_computing`, `public_phase_precision`,
`phase_bits_to_lut`, and `photo_noise_comparison`; the overview is
`project_overview`. Rendering uses the committed outputs, so no native compiler
or new measurement is required. See [dependencies](../requirements.txt).

All scenes receive full-size and 720-pixel poster reviews. The validator checks
actual main-region motion, all three ripple examples, real floor quantization,
source-data consistency, unchanged previous files, document links, English
publication text and full decoded streams. GIF source comparisons catch stale
canvases/palette errors; first/last comparisons check loop continuity. Review
frames for this edition are in [public_visuals](../results/public_visuals).
The current three-panel precision frames and their check record are in
[conventional_comparisons](../results/conventional_comparisons).

Encoded-frame review caught and corrected an end-card text overlap and a GIF
palette that had reduced the amber carry to gray. The final end card uses a
clean background, and decoded GIF checks explicitly verify that amber survives.

First-glance clarity is an author/independent-agent visual QA judgment. No
human user study measured a 3–5-second comprehension rate. Neither attractive
motion nor frame-difference statistics establish scientific superiority.

The broader research boundaries remain those in [paper_review.md](paper_review.md),
[source_alignment.md](source_alignment.md) and [hardware.md](hardware.md). No
new paper result, physical PIM energy/area/performance, complete PLP algorithm,
super-resolution or universal FP32 advantage is established by this edition.
