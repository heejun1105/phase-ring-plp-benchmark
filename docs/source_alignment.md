# Source-to-implementation alignment

The owner-supplied [English Paper VIII](../paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf), dated September 16, 2026, is the primary reference. Its SHA-256 is `d743c111e16aef248092c8bb077ae6edf79942103f6810c3bc4180e3e57faefc`. It is the English edition already reviewed during implementation. [Comparison with the earlier translation](paper_comparison.md) found matching equations, code and table values. Source page numbers below now refer to English.

The reference is documented in [source_manifest.json](../results/source_manifest.json). Paper VIII occupies pages 1-5; appended Paper IX occupies pages 6-9. The authorized English PDF is included unchanged. The translation, extracted text and source-page renderings are not included.

| Source location | Paper operation or claim | Repository implementation | Status |
| --- | --- | --- | --- |
| VIII II.A, Eq. (1), p. 1 | Floor phase quantization, modulo N | `src/phase_ring/quantize` | Implemented; negative-angle and wrap cases tested |
| VIII II.A, Eq. (2), p. 2 | Unit-phasor multiplication as modular phase addition | `src/phase_ring/add`; `src/conventional/multiply` | Implemented for unit magnitude only |
| VIII II.B, Eq. (3)-(4), p. 2 | Natural 10/11-bit overflow | `hardware/phase_adder.v`; explicit NumPy mask | Exhaustive software addition checks; RTL simulation not run |
| VIII VII.B, Listing 2, p. 4 | Scalar sine Q15 lookup | `src/phase_ring/paper_step`; generated sine HEX files | Every LUT entry compared with the displayed Python expression |
| VIII VII.A, Listing 1, p. 4 | Registered 1024 x 16-bit memory read | `hardware/phase_adder.v` | Adapted with explicit LUT initialization and 11-bit option |
| VIII VI, Table I, p. 4 | Cell area, energy and FO4 | Labeled paper estimates in README and animation | No independent hardware measurement |
| VIII III, Eq. (5), p. 2; IX B, Eq. (B1), p. 6 | Plane surface action and entropy absorption | Local Wiener shrinkage, 5x5 neighborhood | Independently designed substitute; not an equation discretization |
| IX B, Eq. (B2), p. 7; C Eq. (C1), p. 8 | Prime-orbit filtering | Guided local smoothing, 5x5 neighborhood | Independently designed substitute; no prime-orbit erasure claim |
| IX B, Eq. (B3), pp. 6-7 | Dirac feature localization | Clipped 10-bit intensity quantization | Independently designed substitute; no sub-pixel recovery claim |
| IX B, Eq. (B4), p. 7 | Unified PLP master operator | Not implemented | Image potential, finite operators and reconstruction rules are insufficiently specified |
| VIII Eq. (6), p. 3; IX Eq. (C2), p. 8 | Contraction and 4-6 iteration recovery | `scripts/audit_claims.py` | Numerical bound audit only, not a PLP solver |
| IX D/E, p. 8; Table II, p. 9 | 4K/8K performance, PSNR, SSIM and pixel energy | Separate paper-estimate table | Unverified paper claims, not inserted into measured CSV values |

## What was rebuilt after source confirmation

- Source identity is now explicit and machine-checkable; outdated unresolved-source wording is removed.
- The computational animation adds all three requested rollover examples and a clear connection to Eq. (1)-(4) and Listing 2.
- The denoising animation shows actual Plane, Line and Point intermediate images, then final results. Text, narrow-line and small-object crops are shown alongside the real photograph.
- Intermediate-stage image quality is retained in `results/stage_quality.csv`. The stage tour runs at presentation pace; no stage-specific processing times are invented.
- The full CPU and image benchmark suite is rerun. Raw repetitions, regenerated English tables and new media all derive from the same current run.

## V3 extension

The six-animation gallery now separates conceptual architecture, measured speed, exact overflow/LUT addressing, experimental noise processing, actual quantization, and legacy/V2 ablation. `src/benchmark/visual_study.py` expands testing to six content classes and 54 noisy cases. V1 remains unchanged; V2 removes the guided pass to expose its quality/edge/latency tradeoff, rather than claiming a new paper-derived PLP algorithm. `native/benchmark.cpp` adds a separately measured fused, preallocated CPU study. No new source-paper equation or hardware performance has been invented. See [visual_study.md](visual_study.md) and [visual_quality.md](visual_quality.md).

## Local source check

```bash
python scripts/verify_source.py paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf
```

This computes a hash only; it neither reads document instructions as commands nor copies or uploads the PDF. A different digest returns a nonzero exit code. Full methodological and theoretical limits remain in [paper_review.md](paper_review.md) and [methodology.md](methodology.md).
