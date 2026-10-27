# Conventional FP32 alongside both phase settings

The full precision versions below compare three methods, with a full-size blue
conventional path beside Z1024 and Z2048. The conventional result is no longer
only a white guide or a number in the footer. The same inputs and output-angle
scale are used for every path. The article uses shorter precision and output-wave
edits without their repeated timing cards. [Article reproduction](reproduction.md)
describes those cuts; the [media archive](media_archive.md) links the full versions.

| Current video | What it shows |
| --- | --- |
| phase_precision_comparison | Three returned-angle curves on one shared plot |
| public_phase_precision | Three equal conventional/coarse/fine panels |
| angle_snap_targets | Three equal output tracks following one ideal target |
| fp32_and_phase_outputs | Three actual waves, then a common zoom near their zero crossings |

## Conventional method and the two lookup settings

The conventional control adds the two raw angles, evaluates cosine and sine,
then writes complex<float> output. It is the existing optimized native control,
not a deliberately slower extra-work implementation. The label FP32 refers to
the output channels; the raw angles and trigonometric evaluations use double
precision. This is not a pure float32 trigonometric-throughput measurement.

The ring paths floor-quantize each input separately, add their indices modulo
1024 or 2048, read paired signed-Q15 cosine/sine and restore complex64 output.
The curves and target pins now include Q15 reconstruction, rather than plotting
only ideal bin angles. Small Q15 overshoots at a boundary are retained.

The white ideal input is a reference, not a fourth measured method. FP32 has a
small real rounding error, often below one display pixel. The videos report it
numerically instead of inventing a visible gap or calling it zero. All three
methods have identical angle or waveform magnification on a given frame.

| Recorded native path, 10M products | Median time | Angular RMSE |
| --- | ---: | ---: |
| Conventional FP32, optimized angle sum | 195.6071 ms | 1.1882345e-8 rad |
| Z1024, Q15 output | 36.9522 ms | 0.0066173594 rad |
| Z2048, Q15 output | 33.2588 ms | 0.0033106281 rad |

These are retained measurements from one C++ CPU run. Accuracy uses the first
200,000 input pairs of that run. Timing is the median of nine repetitions after
two warm-ups. No new benchmark was collected for these animations. Table setup
and allocation are outside the recorded steady-state timing; quantization,
lookup and restoration are inside. [Native audit](native_audit.md) contains
dispersion, the separate four-trig baseline, compiler details and the repeat
that reversed the ranking of the two lookup sizes.

## Demonstration inputs are separate from the measured sample

The single-input plots use a shared 0-2.109375-degree window. The phase at a
point is atan2 of the actual reconstructed real/imaginary channels. The plots
are mathematical illustrations, not error distributions measured from the
animated trajectory.

The two-input wave example uses 0.29° + 0.29°. Its reconstructed phases are
approximately 0.5800000219° for FP32, 0° for Z1024 and 0.3514712570° for Z2048.
The last value comes from the actual Q15 word, not the ideal 0.3515625° bin.
All displayed waves use their actual complex output amplitude and phase.

Near-coincident waves are first shown at normal scale. A common zoom then
reveals their different zero crossings. The final shared window is
[-0.700,+0.150] degrees horizontally and [-0.015,+0.015] in wave value. The
intermediate zoom uses one common range large enough to contain all three
curves; no path is normalized or enlarged independently. Moving cursors do
not encode CPU execution speed.

The C++ loop and the animated NumPy examples implement the same precision
policy, but the small demonstration inputs are not the benchmark's recorded
200,000-pair sample. Native RMSE is read from its CSV, not recomputed from the
toy example or silently mixed with the NumPy timing experiment.

## Preserved earlier versions

The original GIF/MP4 pairs remain unchanged under these names and are linked
in the media archive:

- `legacy_two_settings_phase_precision`
- `legacy_two_settings_public_precision`
- `legacy_two_settings_angle_targets`

The original frame functions remain available as `precision_legacy` or
`frame_legacy`. The archive registry checks the exact original media hashes
before any current video is overwritten. Numerical algorithms, native C++
source, measurement CSVs and image-filter data are unchanged.

## Reproduce and check

```bash
python -m scripts.render_conventional_comparisons --preview-only
python -m scripts.render_conventional_comparisons
python -m scripts.public_gallery
python -m scripts.validate_conventional_comparisons
```

The renderer updates only the three named precision videos and adds the
three-wave comparison. New review frames and records are stored in
[results/conventional_comparisons](../results/conventional_comparisons).
The GIFs are 960x540 at nominal 25 fps; MP4s are 1920x1080 at 24 fps. The current
durations are 12, 15, 16 and 14 seconds. Each final 0.8 seconds blends to the start.

These comparisons establish a CPU time/precision tradeoff for unit-magnitude
phase products. They do not establish an advantage for every FP32 workload,
physical PIM speed, circuit energy or a complete PLP image-processing method.
