"""Data-derived final-refinement README, native cost figure and presentation review."""
from pathlib import Path
import csv,json
from scripts.build_report import table

ROOT=Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def main():
    if json.loads((ROOT/'results/source_manifest.json').read_text())['source_id']=='VIII-EN':
        from scripts.public_gallery import main as current_gallery
        current_gallery()
        return
    native={r['method']:r for r in read('native_audit_benchmark.csv') if int(r['n'])==10000000}
    accuracy={r['method']:r for r in read('native_audit_accuracy.csv') if int(r['n'])==10000000}
    old={r['method']:r for r in read('native_benchmark.csv') if int(r['n'])==10000000}
    numpy={r['method']:r for r in read('benchmark.csv') if int(r['n'])==10000000}
    summary=json.loads((ROOT/'results/visual_study/study_summary.json').read_text())
    four='FP32 four-trig product';summed='FP32 summed-angle trig';z1='Z1024 Q15 end-to-end';z2='Z2048 Q15 end-to-end'
    def ms(m):return float(native[m]['median_ms'])
    def ratio(m,ref=four):return ms(ref)/ms(m)
    methods=[four,summed,z1,z2,'Z2048 float LUT control']
    nt=table(['Native path / 10M products','Median ms','Sample SD ms','M products/s','Angular RMSE rad'],
        [[m,f'{ms(m):.3f}',f"{float(native[m]['std_ms']):.3f}",f"{1e4/ms(m):.2f}",f"{float(accuracy[m]['angular_rmse_rad']):.3e}"] for m in methods])
    npt=table(['NumPy CPU path / 10M','Kernel ms','Raw angles to complex64 ms'],[
        [m,f"{float(numpy[k]['median_ms']):.3f}",f"{float(numpy[e]['median_ms']):.3f}"] for m,k,e in
        [('FP32','FP32 kernel','FP32 end-to-end'),('Z1024','Z1024 add','Z1024 end-to-end'),('Z2048','Z2048 add','Z2048 end-to-end')]])
    qt=table(['54-case arithmetic mean','PSNR dB','SSIM','Custom edge score','Mean timing median ms'],[
        [m,*[f'{summary[m][k]:.3f}' for k in ['psnr_db','ssim','edge_preservation','median_ms']]] for m in ['Bilateral','Legacy V1','Prototype V2']])
    README=f'''# Phase-Ring PIM & PLP Engine

**Visualizing Modular Phase Computing, Processing Efficiency, and Experimental Signal Processing**

Executable unit-phase arithmetic, independently measured CPU workloads, and clearly labeled experimental image processing. Start with the measured race; then follow the bits and memory address.

### 1. Native C++ Performance Comparison

![Native C++ performance comparison](animations/native_cpp_performance.gif)

**10 million shared phase products.** Z1024 / Z2048 take **{ms(z1):.2f} / {ms(z2):.2f} ms**, versus **{ms(four):.2f} ms** for the four-trig product baseline (**{ratio(z1):.2f}x / {ratio(z2):.2f}x** shorter median runtime). The mathematically equivalent **angle-sum + two-trig control takes {ms(summed):.2f} ms**, reducing the ratios to **{ratio(z1,summed):.2f}x / {ratio(z2,summed):.2f}x**. All use float64 angle inputs and complex<float> outputs; ring outputs include floor/Q15 approximation. This specific CPU workload does not measure general FP32 or physical PIM acceleration.

[1080p MP4](animations/video/native_cpp_performance.mp4) · [Renderer](scripts/visualize_v4.py) · [C++ code](native/audit_benchmark.cpp) · [New data](results/native_audit_benchmark.csv) · [Audit and reproducibility](docs/native_audit.md)

### 2. Phase Overflow & SRAM LUT

![Phase overflow and SRAM LUT](animations/phase_overflow_lut.gif)

**Direct arithmetic reproduction:** addition, discarded carry and addressed Q15 table remain linked. [MP4](animations/video/phase_overflow_lut.mp4) · [Renderer](scripts/visualize_v3.py) · [RTL](hardware/phase_adder.v) · [Reference vectors](results/reference_vectors.csv)

### 3. Computational Architecture

![Computational architecture](animations/computing_architecture.gif)

**Conceptual dataflow with real values:** both paths reconstruct complex output. Block count and editorial pacing do not imply physical latency. [MP4](animations/video/computing_architecture.mp4) · [Renderer](scripts/visualize_v3.py) · [Model](src/phase_ring/__init__.py) · [Vectors](results/reference_vectors.csv)

## A. NumPy CPU Benchmark

![NumPy benchmark speed race](animations/benchmark_speed_race.gif)

{npt}
Kernel outputs differ: FP32 returns complex values; masked integer addition returns indices. The same pre-encoded complex-output comparison is **{float(numpy['FP32 kernel']['median_ms']):.2f} ms FP32** versus **{float(numpy['Z1024 encoded-to-complex']['median_ms']):.2f} ms Z1024 + LUT**. NumPy uses separate array operations and allocations; its input dataset differs from native C++. These are separate experiments.

[Race MP4](animations/video/benchmark_speed_race.mp4) · [Renderer](scripts/visualize_v3.py) · [Code](src/benchmark/run.py) · [Data](results/benchmark.csv) · [All measured results](docs/measurements.md)

## B. Optimized Native C++ Benchmark

{nt}
Same inputs and output representation within this new audit, preallocated fused loops, one CPU thread, `-O3 -std=c++17`, no fast-math. Two warm-ups and nine randomized repeats. LUT construction and allocation are excluded; quantization, table access and output restoration are timed. The float-LUT control is also quantized, not full-precision FP32.

The retained earlier native run measured **{float(old['FP32 end-to-end']['median_ms']):.2f} / {float(old['Z1024 end-to-end']['median_ms']):.2f} / {float(old['Z2048 end-to-end']['median_ms']):.2f} ms**. It is stored separately and never averaged with the new audit. A separate 10M repeat changed medians by up to 10.32% and reversed the Z1024/Z2048 speed ranking. Fewer transcendental evaluations, quantized representation, fused memory passes and compiler choices all affect the gap. The new two-trig control exposes the baseline dependence; it does not isolate an intrinsic adder advantage.

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

{qt}
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
'''
    (ROOT/'README.md').write_text(README,encoding='utf-8')
    measures=ROOT/'docs/measurements.md';text=measures.read_text(encoding='utf-8').split('\n## Final native control audit')[0]
    text+='\n## Final native control audit\n\n'+nt+'\nThis is a separate nine-repeat run. Do not merge it with the earlier seven-repeat native results above. [Scope, optimized control, compiler and cache audit](native_audit.md).\n'
    measures.write_text(text,encoding='utf-8')
    qp=ROOT/'docs/visual_quality.md';q=qp.read_text(encoding='utf-8').split('\n## Final refinement review')[0]
    q=q.replace('Overflow/LUT, architecture and speed race lead the README:','The initial gallery used overflow/LUT, architecture and speed race:')
    q=q.replace('- Noise: one predeclared case, synchronized crop/zoom, fixed intensity range and shared error scales. The scan line is editorial. Full-resolution float outputs determine all metrics; display heatmaps are never individually normalized.','- Noise (initial version): four-column imagery followed by error maps. The final revision is described below. Full-resolution float outputs determine all metrics; display heatmaps are never individually normalized.')
    q+='''
## Final refinement review

The original 30 full-size frames and all six 720-pixel posters were reviewed. Architecture, overflow/LUT, NumPy race, precision and edge ablation are preserved byte-for-byte. The old noise demo spent 8 of 12 seconds on heatmaps, with four small image panels; the replacement gives actual images most of the timeline. No denoising algorithm or quality/timing CSV changed.

The README now opens with native C++, then overflow/LUT and architecture. The native race uses a common linear replay of new medians; completion counters assume uniform progress and are editorial, not instrumented execution traces. The giant ratios always name the four-trig baseline. A separate angle-sum/two-trig control is shown before accuracy, making baseline dependence explicit. Input angles and transcendental math are double precision; the output container is complex<float>. This is not a pure FP32 arithmetic throughput claim.

The image-first noise revision uses completed real outputs, identical crop/display conditions per comparison, labeled editorial wipes, clean-reference crops and later common-scale pixel/edge errors. The final full-suite summary exposes both V2 quality losses and time/edge gains. Edge score is custom and not a standard quality metric. See [revision details](noise_visual_revision.md).

Native and revised noise media run 15 seconds; the five retained demos run 12 seconds. Both new sequences blend to their opening frame over the final 0.8 seconds. Validation decodes full MP4 streams, verifies GIF timing/loop metadata, compares decoded GIF pixels against the source renderer and checks first/last-frame continuity. Size optimization uses a shared palette and delta frames rather than individual image enhancement.
'''
    qp.write_text(q,encoding='utf-8')
    envp=ROOT/'results/visualization_environment.json';env=json.loads(envp.read_text())
    env['duration_seconds']={'retained':12,'native_cpp_performance':15,'noise_reduction_comparison':15}
    env['gif_frame_ms']={'retained':80,'native_cpp_performance':100,'noise_reduction_comparison':100}
    envp.write_text(json.dumps(env,indent=2),encoding='utf-8')
    print('Built final hero order, separate evidence sections and image-first supplement.',flush=True)

if __name__=='__main__':main()
