"""Build a visual-first English README and separate, data-derived technical reports."""
from pathlib import Path
import csv,json,statistics,collections,importlib.metadata
from scripts.build_report import table
from scripts.visualize_v3 import NAMES
ROOT=Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def avg(rows,key):return statistics.mean(float(r[key]) for r in rows)

def main():
    b=read('benchmark.csv');native=read('native_benchmark.csv') if (ROOT/'results/native_benchmark.csv').exists() else []
    expanded=read('expanded_noise.csv');ab=read('noise_ablation.csv');env=json.loads((ROOT/'results/environment.json').read_text())
    size=max(int(r['n']) for r in b);largest={r['method']:r for r in b if int(r['n'])==size}
    def small_table(rows):
        return table(['Method','Kernel only (ms)','End-to-end (ms)'],[[name,f"{float(rows[k]['median_ms']):.3f}",f"{float(rows[e]['median_ms']):.3f}"] for name,k,e in
            [('FP32','FP32 kernel','FP32 end-to-end'),('Z1024','Z1024 add','Z1024 end-to-end'),('Z2048','Z2048 add','Z2048 end-to-end')]])
    groups={m:[r for r in expanded if r['method']==m] for m in ['Gaussian','Bilateral','Median','Legacy V1','Prototype V2']}
    noise_table=table(['Method','Mean PSNR (dB)','Mean SSIM','Mean edge score','Mean timing median (ms)'],
        [[m,*[f'{avg(rs,k):.4f}' for k in ['psnr_db','ssim','edge_preservation','median_ms']]] for m,rs in groups.items()])
    details='# Independently measured results\n\n'
    details+=f"## NumPy CPU run\n\n{env['cpu_model']}; Python {env['python']}; NumPy {env['packages']['numpy']}. Two warm-ups and seven randomized repetitions. The supplied NumPy measurements remain the valid pre-redesign run; they were reviewed and preserved rather than presented as newly collected. Expanded image and native runs are new.\n\n"
    details+=table(['N','Method','Mean ms','Median ms','Sample SD ms','M products/s','Input MiB','Incremental traced peak MiB'],
        [[r['n'],r['method'],*[f'{float(r[k]):.5f}' for k in ['mean_ms','median_ms','std_ms']],f"{float(r['ops_per_sec'])/1e6:.2f}",f"{int(r['input_bytes'])/2**20:.2f}",f"{int(r['traced_peak_alloc_bytes'])/2**20:.2f}"] for r in b])
    details+='\nInteger kernels output indices; FP32 outputs complex values. See encoded-to-complex rows for the same output representation. Full end-to-end paths use identical raw angle inputs and complex64 outputs, with quantization error in the ring branch. Memory is scoped input storage and incremental traced allocation, not full-machine peak or physical SRAM. Raw repetitions: [NumPy samples](../results/timing_samples.csv).\n\n'
    details+='## Numerical error\n\n'+table(['N','Method','Samples','Angular RMSE rad','Max angular error rad'],[[r['n'],r['method'],r['evaluated_samples'],r['angular_rmse_rad'],r['max_angular_error_rad']] for r in read('accuracy.csv')])
    if native:
        details+='\n## Separate fused, preallocated C++ run\n\n'+table(['N','Method','Median ms','Sample SD ms','M products/s'],[[r['n'],r['method'],f"{float(r['median_ms']):.5f}",f"{float(r['std_ms']):.5f}",f"{float(r['ops_per_sec'])/1e6:.2f}"] for r in native])
        details+='\nNative inputs differ from NumPy. Fusion and preallocation differ too. This is not an isolated language-speed comparison. [Methodology and reproduction](native_benchmark.md), [compiler environment](../results/native_environment.json), [raw native samples](../results/native_samples.csv), [native errors](../results/native_accuracy.csv).\n'
    details+='\n## Expanded 54-case image study\n\n'+noise_table
    abgroups={m:[r for r in ab if r['method']==m] for m in sorted({r['method'] for r in ab})}
    details+='\n## Independently timed ablations\n\n'+table(['Full callable','Mean PSNR dB','Mean SSIM','Mean edge score','Mean timing median ms'],[[m,*[f'{avg(rs,k):.5f}' for k in ['psnr_db','ssim','edge_preservation','median_ms']]] for m,rs in abgroups.items()])
    details+='\nAll aggregate quality is arithmetic mean of per-case quality; time is the mean of per-case medians. It is not pooled-MSE PSNR or a pooled timing median. Full raw quality, time dispersion and seed-specific results are retained in [expanded CSV](../results/expanded_noise.csv), [expanded timing samples](../results/expanded_noise_samples.csv), [ablation CSV](../results/noise_ablation.csv), and [ablation timing samples](../results/noise_ablation_samples.csv). [Study interpretation](visual_study.md).\n'
    (ROOT/'docs/measurements.md').write_text(details,encoding='utf-8')
    titles=['Computational architecture','Real CPU speed race','Phase overflow and SRAM LUT','Noise reduction and error maps','Quantization and precision','Edge preservation and ablation']
    scopes=['Conceptual dataflow + real numerical example','Measured NumPy medians; kernel and full pipeline','Bit-exact modular arithmetic and Q15 lookup','Experimental prototype; common-scale errors','Real floor quantization and complex64 reference','Legacy V1 versus detail/latency V2']
    code_paths=['src/phase_ring/__init__.py','src/benchmark/run.py','hardware/phase_adder.v','src/benchmark/visual_study.py','src/phase_ring/__init__.py','src/plp/__init__.py']
    data_paths=['results/reference_vectors.csv','results/benchmark.csv','results/reference_vectors.csv','results/expanded_noise.csv','results/precision_sweep.csv','results/noise_ablation.csv']
    gallery=table(['Demo','Watch GIF','1080p H.264','Evidence / code / data'],[[title,f'[GIF](animations/{name}.gif)',f'[MP4](animations/video/{name}.mp4)',f'{scope}; [code]({code}), [data]({data})'] for name,title,scope,code,data in zip(NAMES,titles,scopes,code_paths,data_paths)])
    representative=json.loads((ROOT/'results/representative_case.json').read_text())
    native_note=''
    if native:
        nb={r['method']:r for r in native if int(r['n'])==10000000}
        native_note=f"A separate optimized C++ run is included: at 10M products its raw-angle medians are FP32 **{float(nb['FP32 end-to-end']['median_ms']):.2f} ms**, Z1024 **{float(nb['Z1024 end-to-end']['median_ms']):.2f} ms**, Z2048 **{float(nb['Z2048 end-to-end']['median_ms']):.2f} ms**. Native loops are fused and preallocated, so these numbers cannot be attributed to language alone. [Native method and reproduction](docs/native_benchmark.md)."
    readme=f'''# Phase-Ring PIM & PLP Engine

**Watch unit-phase multiplication become modular addition, bit truncation and an addressed LUT read.**

Executable CPU models and honest measurements inspired by Paper VIII. The circuit views are conceptual; the denoisers are explicitly experimental. No fabricated PIM chip is demonstrated.

### Add -> overflow -> memory address

![Phase overflow and addressed SRAM LUT](animations/phase_overflow_lut.gif)

**Direct arithmetic reproduction.** A rotating phase dial, 10/11-bit registers and a selected LUT word stay linked across all three required rollover examples.

### The same inputs take different paths

![Computational architecture](animations/computing_architecture.gif)

**Conceptual circuit animation with real values.** Both branches restore complex output; paired Q15 lookup and quantization are explicit. Editorial pacing and block count do not imply a speed advantage.

### Race the measured CPU paths

![Real computational speed race](animations/benchmark_speed_race.gif)

**Independently measured results.** Four workload sizes, two distinct scopes: arithmetic kernels first, then the full raw-angle-to-complex pipeline. Slower ring results are retained.

## Demo gallery

{gallery}
All six masters are 1920x1080, H.264, 24 fps and 12 seconds. GIFs are 960x540, looping at a nominal 12.5 fps. The three hero GIFs total approximately {sum((ROOT/'animations'/f'{n}.gif').stat().st_size for n in ['phase_overflow_lut','computing_architecture','benchmark_speed_race'])/1e6:.2f} MB. [Shared animation renderer](scripts/visualize_v3.py) · [Presentation semantics and quality review](docs/visual_quality.md).

### See the precision cost

![Phase quantization and precision](animations/phase_precision_comparison.gif)

A 4-degree window magnifies the true floor-quantization steps. Z1024 resolves 0.3515625 degrees per bin; Z2048 resolves 0.17578125. The orange gaps are actual floor error. Measured product RMSE is reported separately from this single-input illustration.

### Image processing: a research supplement

The image demos compare Clean Original, Noisy Input, Bilateral and a **PLP-Inspired Experimental Prototype - Not a Validated Implementation of the Original PLP Equations**. They use synchronized zooms, actual pixel/edge errors, true profiles and measured processing time. They are kept out of the hero section because this study does not establish general denoising superiority.

[Noise GIF](animations/noise_reduction_comparison.gif) / [MP4](animations/video/noise_reduction_comparison.mp4) · [Ablation GIF](animations/edge_preservation_comparison.gif) / [MP4](animations/video/edge_preservation_comparison.mp4)

![Full-suite quality, edge and latency tradeoffs](results/visual_study/suite_tradeoffs.png)

Legacy V1 remains available unchanged. V2 removes its second spatial smoothing pass: mean edge fidelity and runtime improve, while mean PSNR and SSIM decline. This is an exposed tradeoff, not a universal quality improvement. The fixed microtext example has V2-minus-Bilateral PSNR **{representative['psnr_v2_minus_bilateral']:+.3f} dB**, ranking **{representative['rank_ascending_psnr_gain']}/{representative['total_cases']}** in ascending gain. It was declared before quality comparison, not selected as the best case. [Full image study and ablation](docs/visual_study.md).

## Independently measured CPU results

At {size:,} products on {env['cpu_model']}, NumPy {env['packages']['numpy']}, two warm-ups and seven repetitions:

{small_table(largest)}
**Kernel outputs differ:** FP32 returns complex values, integer addition returns indices. With common pre-encoded complex output at {size:,}, FP32 takes **{float(largest['FP32 kernel']['median_ms']):.2f} ms**, Z1024 + LUT **{float(largest['Z1024 encoded-to-complex']['median_ms']):.2f} ms**. Full-pipeline timings include input conversion, quantization, LUT lookup and restoration. These CPU results do not validate hardware energy, area or in-memory performance.

{native_note}

[All sizes, dispersion, throughput, memory and accuracy](docs/measurements.md) · [NumPy environment](results/environment.json) · [Raw samples](results/timing_samples.csv)

## Implementation and evidence boundaries

- **Paper implementations / faithful arithmetic:** Eq. (1)-(4), 10/11-bit masked addition, Listing 2 signed-Q15 sine LUT, adapted Listing 1 RTL with deterministic memory initialization. All modular input pairs are checked in software.
- **Independent experimental design:** V1 local Wiener + guided smoothing + intensity quantization; V2 local Wiener + intensity quantization. Neither implements the PLP master equation, prime-orbit erasure, entropy absorption or Dirac sub-pixel recovery.
- **Paper-Reported Estimates:** approximately 0.015 pJ/op and 270 um^2 for a 10-bit adder (VIII Table I); 48.6 dB PSNR, 0.993 SSIM and 0.036 pJ/pixel (appended IX Table II). No independent implementation evidence for those hardware/image claims was supplied. They never populate the measured CSV files.

[Source-to-code alignment](docs/source_alignment.md) · [Full paper review](docs/paper_review.md) · [Missing PLP definitions and image-study limits](docs/visual_study.md) · [RTL status](docs/hardware.md)

## Reproduce

Use Python 3.12. Commands below run from the repository root. A full run writes new current results; preserved measurements remain under `results/archive/pre-v3-db8bbe5/` and in the backup branch.

```bash
python -m venv .venv
# Windows: .venv/Scripts/Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/reproduce.py
```

```bash
# Optional fused native CPU benchmark:
python -m pip install -r requirements-native.txt
python scripts/reproduce.py --native

# Reuse measurements and rebuild all six animations:
python scripts/reproduce.py --skip-benchmark

# Quick compute sizes / 3 repetitions; expanded image suite retained:
python scripts/reproduce.py --quick

python -m unittest discover -s tests -v
python -m scripts.validate_v3
python scripts/verify_source.py /path/to/reference.pdf
```

The normal NumPy/expanded-image reproduction does not require a compiler. Native measurements are a separately requested step. First example-data access may require internet. Cross-platform fonts may alter generated text fixtures; committed clean images and fixture hashes identify the supplied run. [Methodology](docs/methodology.md), [image experiment](docs/visual_study.md), [native experiment](docs/native_benchmark.md).

## Source, limitations and next steps

The user-designated nine-page Korean translation of Kim Chul's Paper VIII, dated October 1, 2026, is fingerprinted in [source_manifest.json](results/source_manifest.json). VIII is pages 1-5; the appended IX signal/image-processing paper is pages 6-9. The separate English edition is dated September 16, 2026. Original PDFs are excluded.

The paper's unspecified discrete PLP estimator prevents a faithful full image implementation. CPU benchmarks do not validate a physical PIM architecture. The supplied RTL bench has not been run; no synthesis, FPGA or silicon power/area/timing result is claimed. The expanded study is six grayscale images with clipped additive Gaussian noise, not general video/RAW/super-resolution validation. The source archive DOI is a placeholder.

Next: obtain the complete discrete PLP algorithm and source experiments, expand independently licensed images/noise models, run documented RTL/synthesis and memory-macro validation, then measure physical system energy. Project-wide license selection remains pending. [LICENSE](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md).
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    quality='''# Visualization review and presentation semantics

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
'''
    (ROOT/'docs/visual_quality.md').write_text(quality,encoding='utf-8')
    versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','opencv-python-headless','scikit-image','Pillow','imageio','imageio-ffmpeg','matplotlib']}
    (ROOT/'results/visualization_environment.json').write_text(json.dumps(dict(packages=versions,master_size=[1920,1080],master_fps=24,gif_size=[960,540],gif_frame_ms=80,duration_seconds=12,fonts='Segoe UI / Consolas on supplied Windows host; DejaVu fallback; font binaries excluded'),indent=2),encoding='utf-8')
    inventory=[]
    for name in [*versions,'ziglang']:
        try:m=importlib.metadata.metadata(name)
        except importlib.metadata.PackageNotFoundError:continue
        inventory.append(dict(package=name,version=importlib.metadata.version(name),license_expression=m.get('License-Expression'),
            license_metadata=(m.get('License') or '')[:1200],license_files=m.get_all('License-File') or [],project_urls=m.get_all('Project-URL') or []))
    (ROOT/'results/visual_dependency_licenses.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    print('Built visual-first README and separate measurement, ablation and quality documents.',flush=True)

if __name__=='__main__':main()
