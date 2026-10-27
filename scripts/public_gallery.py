"""Build the reader-facing README from existing CPU and image measurements."""
from pathlib import Path
import csv,json
from scripts.build_report import table

ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def main():
    b={r['method']:r for r in read('native_audit_benchmark.csv') if int(r['n'])==10000000}
    ms=lambda m:float(b[m]['median_ms'])
    four='FP32 four-trig product';opt='FP32 summed-angle trig';z1='Z1024 Q15 end-to-end';z2='Z2048 Q15 end-to-end'
    timings=table(['Method in this CPU test','Time for 10 million results'],[
        ['Calculate both input waves, then multiply (four sine/cosine evaluations)',f'{ms(four):.2f} ms'],
        ['Add the angles, then calculate the output (optimized)',f'{ms(opt):.2f} ms'],
        ['Use a stored table with 1,024 positions (Z1024)',f'{ms(z1):.2f} ms'],
        ['Use a stored table with 2,048 positions (Z2048)',f'{ms(z2):.2f} ms']])
    summary=json.loads((ROOT/'results/visual_study/study_summary.json').read_text())
    quality=table(['Filter','Mean PSNR (dB)','Mean SSIM','Mean CPU time (ms)'],[
        [label,f"{summary[m]['psnr_db']:.2f}",f"{summary[m]['ssim']:.3f}",f"{summary[m]['median_ms']:.2f}"]
        for m,label in [('Bilateral','Bilateral'),('Legacy V1','V1: with extra smoothing'),('Prototype V2','V2: without that extra pass')]])
    text=f'''# Phase-Ring PIM & PLP Engine

This repository runs two CPU experiments inspired by [Paper VIII](paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf). One tests whether a stored table can replace repeated calculations for wave angles. The other compares filters that remove speckles from an image. The speed figures from the first experiment do not describe the image filters, and neither experiment tests a physical PIM chip.

## Calculation time

![The same work moving from waiting to finished](animations/public_cpu_workflow.gif)

Each row receives the same input for 10 million results. The blocks show equal amounts of work moving into the finished area. Their timing follows recorded CPU medians, slowed down for the video; the moving blocks are an illustration.

{timings}
Calculating both input waves before multiplying took **{ms(four)/ms(z1):.2f} / {ms(four)/ms(z2):.2f} times as long as Z1024 / Z2048** in this run. The optimized formula route took **{ms(opt)/ms(z1):.2f} / {ms(opt)/ms(z2):.2f} times as long**, respectively. The table-based paths return an approximate answer. This applies to a particular task involving angles of unit-strength waves, not all multiplication. Another run reversed the speed ranking of Z1024 and Z2048.

[Watch MP4](animations/video/public_cpu_workflow.mp4) · [Measurement conditions](docs/native_audit.md) · [Data](results/native_audit_benchmark.csv)

## Removing noise from a photograph

![The same noisy photograph and recorded filter results](animations/photo_noise_comparison.gif)

Look at the speckles in the sky and coat, then at the tripod edges and the enlarged details. A filter can remove speckles and also soften real detail. The divider reveals an already completed result; it does not show the algorithm processing the picture step by step.

The video compares a standard Bilateral filter with two experimental filters. V1 adds a smoothing pass after local noise reduction. V2 leaves out that pass: it finishes sooner than V1, but its average PSNR and SSIM are lower. Bilateral is also faster than V2 on the full study average. There is no overall winner established by these tests.

**PLP-Inspired Experimental Prototype — Not a Validated Implementation of the Original PLP Equations**

[Watch MP4](animations/video/photo_noise_comparison.mp4) · [Image-study methods](docs/visual_study.md) · [All cases](results/expanded_noise.csv)

<details>
<summary>Photo quality and processing times</summary>

These are means across 54 noisy cases: six images, three noise levels and three seeds. PSNR and SSIM compare each output with the clean reference; higher values mean a closer match under these metrics. CPU time is the mean of per-case timing medians; lower is faster. The clean reference is used for evaluation, not given to the filters.

{quality}
The study also records a custom edge score. V2 raises that mean score from 0.866 to 0.879 compared with V1, while losing PSNR and SSIM. That score is not a standard perceptual quality measure. [Definitions and limitations](docs/methodology.md) · [Filter code](src/plp/__init__.py)

</details>

## The three explanation videos

These explain the calculation shortcut above. They are not three more performance results, and you can skip the bit-level check when viewing the main results.

**How the calculation changes.** Picture an angle as the position of a hand on a clock. The blue path calculates the waves and multiplies them. The cyan path adds their numbered positions and reads an answer from a stored table. The final waves are close, but not exactly equal; the actual difference is reported as a number. [Animation](animations/public_phase_computing.gif) · [MP4](animations/video/public_phase_computing.mp4)

**What precision the shortcut loses.** A table has a fixed number of positions. Z1024 has 1,024 marks around the circle; Z2048 has twice as many. The staircase shows an input snapping down to a stored angle, or staying there if it is already on a mark. Smaller steps reduce the angle error and require more table entries. This scene is about accuracy, not speed. [Animation](animations/public_phase_precision.gif) · [MP4](animations/video/public_phase_precision.mp4)

**Whether the bits select the right answer.** Going past the last mark returns to the start, as on a clock face. The program numbers its 1,024 marks from 0: after 1023 comes 0. The bit video checks that wraparound, the table address and the stored value. It checks the implementation; it is not another acceleration claim. [Technical animation](animations/phase_bits_to_lut.gif) · [MP4](animations/video/phase_bits_to_lut.mp4)

[A short guide to these demos](docs/understanding_the_demos.md) · [All four calculation scenes in a 40-second video](animations/video/project_overview.mp4)

## Paper and scope

The [English original](paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf), dated September 16, 2026, is included unchanged at the owner's request. It contains Paper VIII on pages 1-5 and the signal/image-processing IX appendix on pages 6-9. It has the same reviewed equations, code and table values as the earlier October 1 Korean translation, with different dates and pagination. The translation is not included. [Comparison record](docs/paper_comparison.md) · [Source hash](results/source_manifest.json)

The masked phase addition and signed-16-bit lookup table are implemented. The image filters are independently designed substitutes: the source does not define enough discrete steps to reproduce the complete PLP image algorithm. The paper's energy, chip area, zero-blur and super-resolution claims have not been validated here. No RTL simulation, synthesis, SRAM chip, FPGA or silicon measurement is reported. [Paper review](docs/paper_review.md) · [Source-to-code mapping](docs/source_alignment.md) · [Hardware status](docs/hardware.md)

## Code, data and reproduction

```bash
python -m venv .venv
# Windows: .venv/Scripts/Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.render_public_visuals --preview-only
python -m scripts.render_story_variants --preview-only
python -m scripts.public_gallery
python -m scripts.validate_public_visuals
python -m scripts.validate_reader_update
python -m scripts.validate_story_variants
```

To regenerate these GIF/MP4 files from the committed data, run `python -m scripts.render_public_visuals` and `python -m scripts.render_story_variants`. They read existing measurements and completed image outputs; they do not collect new benchmark data. MP4s are 1920×1080 at 24 fps; GIFs are 960×540 with playback rates recorded by edition. The new angle stories use 25 fps GIFs, and the photo lens uses 20 fps. Rendering sources and review frames are linked below.

<details>
<summary>Experiment details and rendering sources</summary>

- **NumPy CPU study:** separate array operations, allocation and input conversion. Its integer-add kernel returns an index; the FP32 kernel returns complex values. Those kernels are not equivalent full pipelines. [Measurements](docs/measurements.md) · [CSV](results/benchmark.csv) · [Raw timings](results/timing_samples.csv) · [Environment](results/environment.json)
- **Native C++ study:** fused preallocated loops, float64 input angles and complex<float> output. Tables are built before timing; lookup and Q15 restoration are inside timing. Different accuracy, data generation and allocation policies prevent a language-only speedup claim. [Audit](docs/native_audit.md) · [Original native method](docs/native_benchmark.md) · [Raw timings](results/native_audit_samples.csv) · [Accuracy](results/native_audit_accuracy.csv) · [Compiler inspection](results/native_audit_compiler.json) · [Environment](results/native_audit_environment.json)
- **Phase arithmetic:** the identity applies to unit-magnitude complex signals. Scalar sine storage is 2/4 KiB; the software paired cosine/sine table is 4/8 KiB. [Model](src/phase_ring/__init__.py) · [Reference examples](results/reference_vectors.csv)
- **Image filters:** six grayscale fixtures with clipped Gaussian noise. V1/V2 do not implement the PLP master equation, prime-orbit erasure or Dirac sub-pixel recovery. [Study](docs/visual_study.md) · [Ablations](results/noise_ablation.csv) · [Recorded photo arrays](results/visual_study/camera_outputs.npz)
- **Paper estimates:** approximately 0.015 pJ/op, 270 um² and 4 FO4, plus the IX image claims, are paper-reported values. They are separate from the measured CSVs. [Review](docs/paper_review.md)
- **Renderers:** [Work queues](scripts/visualize_workflow_v5.py) · [Calculation routes](scripts/visualize_public_principle.py) · [Precision](scripts/visualize_public_precision.py) · [Bits and lookup](scripts/visualize_bit_lut_v5.py) · [Photo comparison](scripts/visualize_photo_noise.py) · [Video export](scripts/render_public_visuals.py)

[Frame reviews](results/public_visuals) · [Video validation](results/public_visuals/validation.json) · [Paper and document checks](results/reader_review.json) · [Presentation notes](docs/public_visuals.md) · [Licensing status](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md)

</details>

<details>
<summary>Earlier videos and review records</summary>

[Native timing and accuracy GIF](animations/native_cpp_performance.gif) / [MP4](animations/video/native_cpp_performance.mp4) · [Architecture GIF](animations/computing_architecture.gif) / [MP4](animations/video/computing_architecture.mp4) · [NumPy race GIF](animations/benchmark_speed_race.gif) / [MP4](animations/video/benchmark_speed_race.mp4) · [Overflow GIF](animations/phase_overflow_lut.gif) / [MP4](animations/video/phase_overflow_lut.mp4) · [Precision GIF](animations/phase_precision_comparison.gif) / [MP4](animations/video/phase_precision_comparison.mp4) · [Earlier noise GIF](animations/noise_reduction_comparison.gif) / [MP4](animations/video/noise_reduction_comparison.mp4) · [Edge ablation GIF](animations/edge_preservation_comparison.gif) / [MP4](animations/video/edge_preservation_comparison.mp4)

[Previous visual review](docs/visual_quality.md) · [Noise revision](docs/noise_visual_revision.md) · [Previous validation](results/validation.json) · [Source manifest before the English upload](results/archive/source_manifest_viii_ko.json)

</details>
'''
    from scripts.expand_visual_gallery import expand
    text=expand(text)
    (ROOT/'README.md').write_text(text,encoding='utf-8')
    print('Built README with all existing animations visible and additional story variants.',flush=True)

if __name__=='__main__':main()
