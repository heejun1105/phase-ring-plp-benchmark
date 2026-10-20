# Experimental methodology

This document describes the retained NumPy and original two-image baseline experiment. The current six-image study, ablation and six-animation presentation are documented in [visual_study.md](visual_study.md), [native_benchmark.md](native_benchmark.md) and [visual_quality.md](visual_quality.md). Historical media semantics below refer to `computing_comparison` and `noise_comparison`, which are preserved rather than overwritten by the new gallery.

## Evidence categories

- **Paper-Reported Estimates:** source-paper claims transcribed in `paper_review.md`, without independent validation.
- **Independently Measured Results:** actual software timings, arithmetic errors, and conventional filter results in CSV files.
- **Experimental Prototype Results:** actual outputs of our independently designed PLP-inspired image pipeline. These do not validate the paper's PLP equations.

## Computational workload

The workload is elementwise multiplication of unit complex phasors. One operation means one phase product, irrespective of the number of low-level CPU instructions. Input pairs are float64 angles uniformly distributed in [-pi,pi), from NumPy Generator with seed 20261020. Both branches receive these same angles. Data generation is outside timing. FP32 uses NumPy complex64 (two FP32 channels); modulus indices use uint16 containers with explicit 10/11-bit masking. This is an optimized NumPy comparison on both sides, not Python loops versus vectorization.

Sizes are 10,000; 100,000; 1,000,000; and 10,000,000 elements. Each callable receives two warm-ups and seven timed repetitions. Method order is shuffled on each repetition. `perf_counter_ns` measures wall-clock execution. Allocation is included in each callable, and previous results are released outside timing. This is a single-process CPU benchmark; CPU frequency, OS scheduling, memory allocation/caches, and background activity remain sources of variation. NumPy ufuncs here are elementwise, not BLAS workloads. Thread environment settings and OpenCV's explicit single-thread setting are recorded.

| Stage | Input | Output | Included work |
|---|---|---|---|
| FP32 kernel | Pre-encoded complex64 pairs | complex64 product | NumPy multiply and output allocation |
| ZN add | Pre-encoded uint16 pairs | uint16 modular indices | NumPy add, mask and allocations |
| ZN LUT decode | Precomputed modular indices | complex64 phasor | Two Q15 lookups, scaling and reconstruction |
| ZN encoded-to-complex | Pre-encoded uint16 pairs | complex64 phasor | Modular add and LUT reconstruction |
| FP32 encode pair | Raw float64 angles | Two complex64 arrays | Complex exponentials and casts |
| ZN quantize pair | Same raw float64 angles | Two uint16 arrays | Scale, floor, modulo and casts |
| FP32 end-to-end | Raw angles | complex64 product | Both encodings plus multiplication |
| ZN end-to-end | Same raw angles | complex64 approximation | Both quantizations, add, LUT reconstruction |

Kernel-only outputs have different representations. Their ratio is not a speedup for an identical end-to-end task. Compare encoded-to-complex stages for equivalent output type, or end-to-end stages for common input/output types. Quantization still changes accuracy. Stage medians measured separately need not sum to the end-to-end median because allocation lifetime, cache effects, and measurement conditions differ. No hardware speedup, general MAC equivalence, or energy ratio is inferred.

Mean, median, sample standard deviation (ddof=1), min/max, and operation throughput (N divided by median seconds) are stored. Every raw repetition is retained in `timing_samples.csv`. There is no subtraction of timer overhead or synthetic adjustment of values.

## Accuracy and memory

Accuracy uses the first min(N,200000) pairs from each exact timing dataset; `evaluated_samples` records that sample size. Float64 complex exponentials of summed original angles are the reference. Wrapped angular RMSE and maximum error, complex RMSE, and modulus error are reported. A separate quantized-reference complex RMSE isolates Q15 reconstruction loss. Floor quantization of two inputs can approach 4*pi/N angular error; Q15 truncation introduces additional small error. These results are not interchangeable with a one-bin resolution claim.

`input_bytes` counts just the arrays/table passed to each measured callable. `traced_peak_alloc_bytes` is a separate invocation's incremental tracemalloc peak, including NumPy allocations exposed through its allocator; it excludes existing inputs and untracked native-library storage. It is not total machine RAM, full-process peak RSS, or physical SRAM area. `rss_before_bytes` and `rss_after_bytes` are separate process RSS snapshots including shared benchmark fixtures and interpreter state. Their difference is not a reliable per-kernel memory peak because allocators cache memory. Memory probes occur outside timing. These distinctions are essential when reading the CSV. LUT construction/setup is separately measured in `lut_setup.csv`.

## Denoising workload

Inputs are a 512x512 real camera photograph from scikit-image (`camera`, CC0 by Lav Varshney) and an original 512x512 text/line/dot chart. The saved clean chart avoids font-substitution differences when reviewing the committed results. Regeneration may use Segoe/Arial on Windows or DejaVu on Linux. Source attribution is in `THIRD_PARTY_NOTICES.md`.

For each image, Gaussian standard deviations are 0.03, 0.06, 0.10 in normalized [0,1] units. Noise seeds are 20261020, 20261021, 20261022. The additive noisy image is clipped to [0,1], so near boundaries its residual noise is not an unbounded Gaussian. All filters receive the same float32 noisy array for each case. No clean reference is passed to filtering. The supplied sigma is used by Bilateral and the prototype; this is a known-noise-level experiment, not blind denoising.

- Gaussian: 5x5, spatial sigma 1.0.
- Bilateral: diameter 7, intensity sigma 2*noise_sigma, spatial sigma 2.0.
- Median: 3x3.
- Prototype Plane: 5x5 local Wiener shrinkage `mean + max(var-sigma^2,0)/(var+eps)*(x-mean)`.
- Prototype Line: 5x5 guided local linear smoothing of the Plane output, regularization 0.25*sigma^2.
- Prototype Point: clipping then nearest 10-bit intensity quantization, `round(1023*x)/1023`. This is scalar quantization, not Dirac localization or modular phase mapping.

OpenCV reflect-101 borders are explicitly selected where supported; OpenCV median uses its own replicated boundary treatment. Each full callable is warmed twice and repeated seven times in randomized method order. Preprocessing, file I/O, metrics, and animation rendering are outside filtering time. Prototype timing includes all three stages; no stage is omitted to improve its result. Parameters are fixed across the sweep; this is an illustrative baseline comparison, not an exhaustive optimization contest.

PSNR and SSIM use scikit-image with data_range=1. Edge preservation is explicitly defined as:

`E = 1 / (1 + mean(|Sobel(result)-Sobel(clean)| on strong_edges) / mean(Sobel(clean) on strong_edges))`.

Sobel means gradient magnitude from 3x3 x/y derivatives. Strong edges are locations strictly above the clean gradient's 90th percentile. Higher scores are better, with a perfect match scoring 1. This is a custom reference-based score, not a universal edge quality metric, and can score noisy inputs favorably. PSNR/SSIM and visual review are also needed. Per-case metrics and raw timing samples are retained. Reported aggregate quality is arithmetic mean across noise realizations, not pooled-MSE PSNR. Aggregate time is the mean of per-case timing medians, not a median of all samples. Noise-quality variation and within-case timing deviations are separate quantities. The Noisy input timing is an array-copy control, not a denoising algorithm. Intermediate Plane/Line/Point quality is computed from float32 stage outputs in `stage_quality.csv`; PNG display images are rounded to 8-bit for viewing.

## Animation semantics

Both masters are 1920x1080, H.264/yuv420p, 24 fps, 12 seconds. GIFs are 960x540, 10 fps nominal, looping, with a shared 256-color palette. The last 0.8 seconds crossfade back to the initial frame. An encoder may merge identical GIF frames while preserving duration.

Compute progress uses a common linear stretch of actual median FP32-kernel and Z1024-add durations. The first 3.6 seconds cycle through the three requested exact rollover examples, including retained binary address bits and actual Q15 sine values. Equivalent complex-output and full-pipeline costs then occupy the same lower panel. Numbers for Z2048 and angular error remain visible. Animated arrows illustrate operation structure rather than measured instruction traces.

The noise demonstration uses the identified camera case and text-chart case with sigma=0.06 and seed 20261020. It starts with identical noisy inputs. The right image tours actual Plane output (1.0-2.4 s), Line output (2.4-3.8 s), Point output (3.8-5.2 s), then final reconstruction. These intervals are editorial presentation pace, not measured stage durations. Camera PSNR/SSIM/edge scores switch to the actual displayed stage; the full-pipeline median time is separately labeled. Text, line and dot crops are real results from the second image, not content from the camera photo. The left image reveals the final Bilateral output with an illustrative wipe. Bars on both sides use a common linear stretch of measured full-call medians; neither bars nor wipes claim instrumented pixel or stage traces. A separate text-detail figure shows all filters. All displayed numbers come from CSV files, except explicitly labeled paper estimates.

## Reproducibility limits

The locked Python dependencies and environment JSON identify this run. Other CPUs and package builds will produce different timings. No accelerator, energy meter, physical SRAM macro, foundry PDK, synthesized area, instrumented power model, or complete paper PLP image algorithm was available. The supplied RTL testbench is optional; a lack of simulator execution is recorded separately from passing Python tests. The user-designated source PDF is confirmed in `source_manifest.json`; its bytes match the initial primary reference. This confirmation establishes source identity, not validity of the paper's unverified performance claims.
