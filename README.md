# Phase-Ring PIM & PLP Engine

**Visualizing Modular Phase Computing, Processing Efficiency, and Experimental Signal Processing**

Executable unit-phase arithmetic, independently measured CPU workloads, and clearly labeled experimental image processing. Start with the measured race; then follow the bits and memory address.

### 1. Native C++ Performance Comparison

![Native C++ performance comparison](animations/native_cpp_performance.gif)

**10 million shared phase products.** Z1024 / Z2048 take **36.95 / 33.26 ms**, versus **330.40 ms** for the four-trig product baseline (**8.94x / 9.93x** shorter median runtime). The mathematically equivalent **angle-sum + two-trig control takes 195.61 ms**, reducing the ratios to **5.29x / 5.88x**. All use float64 angle inputs and complex<float> outputs; ring outputs include floor/Q15 approximation. This specific CPU workload does not measure general FP32 or physical PIM acceleration.

[1080p MP4](animations/video/native_cpp_performance.mp4) · [Renderer](scripts/visualize_v4.py) · [C++ code](native/audit_benchmark.cpp) · [New data](results/native_audit_benchmark.csv) · [Audit and reproducibility](docs/native_audit.md)

### 2. Phase Overflow & SRAM LUT

![Phase overflow and SRAM LUT](animations/phase_overflow_lut.gif)

**Direct arithmetic reproduction:** addition, discarded carry and addressed Q15 table remain linked. [MP4](animations/video/phase_overflow_lut.mp4) · [Renderer](scripts/visualize_v3.py) · [RTL](hardware/phase_adder.v) · [Reference vectors](results/reference_vectors.csv)

### 3. Computational Architecture

![Computational architecture](animations/computing_architecture.gif)

**Conceptual dataflow with real values:** both paths reconstruct complex output. Block count and editorial pacing do not imply physical latency. [MP4](animations/video/computing_architecture.mp4) · [Renderer](scripts/visualize_v3.py) · [Model](src/phase_ring/__init__.py) · [Vectors](results/reference_vectors.csv)

## A. NumPy CPU Benchmark

![NumPy benchmark speed race](animations/benchmark_speed_race.gif)

| NumPy CPU path / 10M | Kernel ms | Raw angles to complex64 ms |
| --- | --- | --- |
| FP32 | 26.707 | 765.735 |
| Z1024 | 15.851 | 683.486 |
| Z2048 | 15.061 | 695.404 |

Kernel outputs differ: FP32 returns complex values; masked integer addition returns indices. The same pre-encoded complex-output comparison is **26.71 ms FP32** versus **231.04 ms Z1024 + LUT**. NumPy uses separate array operations and allocations; its input dataset differs from native C++. These are separate experiments.

[Race MP4](animations/video/benchmark_speed_race.mp4) · [Renderer](scripts/visualize_v3.py) · [Code](src/benchmark/run.py) · [Data](results/benchmark.csv) · [All measured results](docs/measurements.md)

## B. Optimized Native C++ Benchmark

| Native path / 10M products | Median ms | Sample SD ms | M products/s | Angular RMSE rad |
| --- | --- | --- | --- | --- |
| FP32 four-trig product | 330.396 | 21.774 | 30.27 | 2.571e-08 |
| FP32 summed-angle trig | 195.607 | 19.642 | 51.12 | 1.188e-08 |
| Z1024 Q15 end-to-end | 36.952 | 4.425 | 270.62 | 6.617e-03 |
| Z2048 Q15 end-to-end | 33.259 | 2.304 | 300.67 | 3.311e-03 |
| Z2048 float LUT control | 20.095 | 2.880 | 497.63 | 3.311e-03 |

Same inputs and output representation within this new audit, preallocated fused loops, one CPU thread, `-O3 -std=c++17`, no fast-math. Two warm-ups and nine randomized repeats. LUT construction and allocation are excluded; quantization, table access and output restoration are timed. The float-LUT control is also quantized, not full-precision FP32.

The retained earlier native run measured **375.66 / 42.00 / 39.26 ms**. It is stored separately and never averaged with the new audit. A separate 10M repeat changed medians by up to 10.32% and reversed the Z1024/Z2048 speed ranking. Fewer transcendental evaluations, quantized representation, fused memory passes and compiler choices all affect the gap. The new two-trig control exposes the baseline dependence; it does not isolate an intrinsic adder advantage.

[Original native method](docs/native_benchmark.md) · [New audit](docs/native_audit.md) · [Raw repeats](results/native_audit_samples.csv) · [Accuracy](results/native_audit_accuracy.csv) · [Compiler diagnostics](results/native_audit_compiler.json) · [Environment](results/native_audit_environment.json)

## C. Mathematical and Architectural Comparison

For unit-magnitude phasors, `exp(i*a) * exp(i*b) = exp(i*(a+b))`. Quantize each angle by `floor(angle*N/(2*pi))`, add and mask by `N-1`, then read paired Q15 cosine/sine. This reproduces the paper's modular phase arithmetic and signed-Q15 table; it is not general complex MAC equivalence. The paired LUT occupies 4 / 8 KiB for N=1024 / 2048; the scalar sine table is 2 / 4 KiB.

![Phase precision comparison](animations/phase_precision_comparison.gif)

True floor-quantization steps in a magnified 4-degree input window. Product RMSE uses two quantized inputs and is reported separately. [MP4](animations/video/phase_precision_comparison.mp4) · [Renderer](scripts/visualize_v3.py) · [Code](src/phase_ring/__init__.py) · [Recorded sweep](results/precision_sweep.csv) · [Source alignment](docs/source_alignment.md)

## D. Paper-Reported Hardware Estimates

Paper VIII reports approximately **0.015 pJ/op, 270 um^2 and ~4 FO4** for a 10-bit adder. The appended IX reports **48.6 dB PSNR, 0.993 SSIM and 0.036 pJ/pixel**. These are **unverified paper estimates**, separate from every measured CPU/image CSV. No SRAM macro, synthesis, FPGA or silicon energy/area/timing validation was performed. CPU ratios cannot validate those claims. [Paper review](docs/paper_review.md) · [RTL status](docs/hardware.md)

## Research Supplement: Faster Processing vs. Noise Removal Quality

![Image-first noise comparison](animations/noise_reduction_comparison.gif)

Large actual-image comparisons come first, followed by synchronized detail crops and shared-scale errors. The sliding boundary is an **editorial wipe between completed outputs**, not an iterative PLP process. [Noise MP4](animations/video/noise_reduction_comparison.mp4) · [Renderer](scripts/visualize_noise_v4.py) · [Code](src/plp/__init__.py) · [All 54 cases](results/expanded_noise.csv) · [Visual revision](docs/noise_visual_revision.md)

**PLP-Inspired Experimental Prototype — Not a Validated Implementation of the Original PLP Equations**

| 54-case arithmetic mean | PSNR dB | SSIM | Custom edge score | Mean timing median ms |
| --- | --- | --- | --- | --- |
| Bilateral | 34.142 | 0.821 | 0.897 | 5.279 |
| Legacy V1 | 33.999 | 0.927 | 0.866 | 12.410 |
| Prototype V2 | 32.686 | 0.862 | 0.879 | 6.082 |

Legacy V1 uses local Wiener shrinkage + guided smoothing + 10-bit quantization; V2 removes guided smoothing. V2 lowers mean runtime and improves this mean edge score, while PSNR and SSIM decline. Bilateral also remains faster than V2 in this study. **Edge score** is a custom Sobel-fidelity score on the strongest clean edges, not a standardized perceptual metric. No general denoising superiority is established.

[Retained edge/latency GIF](animations/edge_preservation_comparison.gif) · [MP4](animations/video/edge_preservation_comparison.mp4) · [Renderer](scripts/visualize_v3.py) · [Ablation data](results/noise_ablation.csv) · [Study, metric definitions and selection policy](docs/visual_study.md)

## Reproduce and verify

Python 3.12; run from the repository root. The original measurements remain unchanged by this refinement. Full remeasurement intentionally writes current-run result files; preserve them before running a new study.

```bash
python -m venv .venv
# Windows: .venv/Scripts/Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-native.txt
python -m scripts.run_native_audit
python -m scripts.visualize_v4
python -m scripts.gallery_report
python -m unittest discover -s tests -v
python -m scripts.validate_v3
```

To repeat the earlier full NumPy/image experiment: `python scripts/reproduce.py`. To reuse all supplied measurements and rebuild media: `python scripts/reproduce.py --skip-benchmark`. [Native audit options](docs/native_audit.md) · [Original methodology](docs/methodology.md) · [Presentation semantics](docs/visual_quality.md) · [Retained-file verification](results/refinement_preservation.json)

Seven current GIF/MP4 pairs are provided: five retained 12-second demos, and the new native and revised noise 15-second demos. MP4: 1920x1080 / 24 fps. GIF: 960x540 / looping. Original legacy media also remains available in Git history and the backup branch.

## Source and limits

The user-designated nine-page Korean translation of Kim Chul's Paper VIII (October 1, 2026) is fingerprinted in [source_manifest.json](results/source_manifest.json). VIII occupies pages 1–5; the appended image-processing IX occupies pages 6–9. Original PDFs are excluded. The source archive DOI is a placeholder. The paper lacks a complete discrete PLP estimator, so V1/V2 are independently designed substitutes; neither validates prime-orbit erasure, entropy absorption or Dirac recovery. Six grayscale images and clipped Gaussian noise do not establish general image/video/RAW performance. Project-wide licensing remains pending. [LICENSE](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md)
