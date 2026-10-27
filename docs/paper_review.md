# Source review and evidence boundaries

## Confirmed source identity

The primary reference is the owner's [English original](../paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf), dated September 16, 2026. Its bytes match the English edition reviewed during implementation. The earlier Korean translation is dated October 1, 2026. Both contain the same reviewed equations, code and table values, with different pagination; [the comparison](paper_comparison.md) records those differences. The owner requested the English PDF be included unchanged. The translation, full extracted text and source-page renderings are not distributed. Page references below use the English edition.

| ID | Source | Pages | SHA-256 |
|---|---|---:|---|
| VIII-KO | Translated Paper VIII, October 1, 2026 | 9 | `249f651810bce6fab84693dd1049a3a551ab15e0b59893b5cd82a0461171ea41` |
| VIII-EN | Paper VIII: Dual-Layer Topological Neuromorphic and Signal Processing Architecture, September 16, 2026 | 9 | `d743c111e16aef248092c8bb077ae6edf79942103f6810c3bc4180e3e57faefc` |
| IX-KO-standalone | Separate translated Paper IX, October 1, 2026 | 4 | `2e58f688fd3dcc6ab4a593a14c957c59fe6d6c8148cbdd7b401249a76e62b47a` |

Both VIII editions contain Paper VIII on pages 1-5 and the appended signal/image-processing Paper IX on pages 6-9. IX-KO-standalone is a different document about geometric decomposition, information theory, and a convergence theorem; its content must not be substituted for the image-processing appendix.

## Paper VIII, section by section

The owner has since supplied [10.5281/zenodo.22782241](https://doi.org/10.5281/zenodo.22782241)
as the Paper VIII archive link. References below to `zenodo.XXXXX` concern the
placeholder printed in the unchanged PDF. The supplied DOI is a paper link;
this update does not claim a separately retrieved code release or new validation
of the paper's hardware and image-processing results.

1. **Abstract and Section I (p. 1):** Two proposed layers combine modular phase arithmetic and a PLP decision engine on a PIM substrate. The text acknowledges domain specialization. This project implements CPU reference models, not a fabricated memory-compute substrate.
2. **Section II (pp. 1-2), Eq. (1)-(4):** Quantization uses a floor followed by modulo N. Unit phasor multiplication becomes angle addition modulo N. For N=1024/2048, 10/11-bit truncation implements the modulo exactly. Our software uses uint16 storage and an explicit mask; a uint16 overflow alone is not a 10-bit overflow. The 0.3515625/0.17578125 degree bin widths are resolution, not a measured end-to-end error. Two separately floored inputs can accumulate almost two bins of angular error.
3. **Section III (p. 2), Eq. (5):** The unified PLP expression combines a surface potential, entropy sum, prime contour integrals, and Dirac localization. It does not define a complete discrete image estimator: the potential, probability estimators, image-to-manifold map, finite contour set, finite-time operator, and reconstruction rules are insufficiently specified. The definitions do not supply executable denoising code.
4. **Section IV (pp. 2-3), Eq. (6) on p. 3:** The proposed 1D address latching does not by itself establish lossless representation of arbitrary multidimensional functions. O(1) indexing after an address is available does not remove preprocessing, representation, or LUT-capacity costs. The stated contraction factor alone also does not establish exact 4-6 iteration convergence; see the numerical audit below.
5. **Section V (pp. 3-4), Eq. (7)-(11):** The paper discusses exponential LUT scaling, phase quantization, a reported SRAM/interconnect power breakdown, and prospective photonic routing. No photonic device, optical experiment, full-chip power trace, layout, or complete PIM macro is supplied in the reviewed files. These are architectural arguments and roadmap claims, not independently reproduced device results.
6. **Section VI (p. 4), Table I:** The paper lists a 28 nm, 1.0 V, TT, 25 C comparison and a footnote asserting standard-cell synthesis. It does not provide the cell library, constraints, synthesis reports, netlist, switching activity, or measurement data needed to reproduce it. We retain its values under **Paper-Reported Estimates**, even where the paper calls them factual or verified. A phase adder and a general FP32 MAC also have different computational semantics.
7. **Section VII (p. 4), Listings 1-2:** Verilog gives a 10-bit addition and a registered read of a 1024 x 16-bit array; Python provides a masked phase sum and a truncated signed-Q15 sine LUT. These establish a small executable arithmetic model. The original RTL does not initialize its LUT: reading it without external initialization yields unknown simulation data. Our adaptation adds generated initialization files and an 11-bit parameterization. It does not demonstrate a physical SRAM macro or measured 1-clock timing closure. Python LUT creation is hoisted out of steady-state timing and measured separately.
8. **Conclusion, declaration, references (p. 5):** The text dedicates disclosed principles/logic to the public domain and refers to a Zenodo DOI ending in `XXXXX`. This is a placeholder, not a usable archive identifier. No verified public code release or supplementary implementation was obtained from that reference. Project license selection remains pending rather than inventing terms.

## Appended Paper IX, sections A-F (pp. 6-9)

The appendix elaborates a plane surface/entropy operation (B1), infinite-time prime-orbit filtering (B2), Dirac point localization (B3), and a unified operator (B4). Section C asserts blur-free denoising, cross-mode erasure, and deterministic super-resolution. Section D maps the proposal to modular registers and a scalar SRAM LUT. Section E and Table II give theoretical/simulation comparison claims without identifiable images, noise distributions, seeds, executable image-processing code, raw outputs, or timing traces. Section F concludes and repeats the defensive-publication declaration and placeholder archive reference.

| Claim | Source | Evidence treatment in this project |
|---|---|---|
| 10-bit adder: ~270 um^2, ~0.015 pJ/op, ~4 FO4 | VIII Table I, p. 4 | Paper-Reported Estimates; no independent synthesis or silicon validation |
| FP32 MAC: ~3500 um^2, 3.70 pJ/op; INT8 MAC: ~480 um^2, 0.20 pJ/op | VIII Table I | Paper baselines; not the CPU phasor product benchmark |
| SRAM 79.5%, interconnect 19.9% energy shares | VIII Section V.B | Unreproduced paper system breakdown |
| 48.6 dB PSNR, 0.993 SSIM | IX appendix Table II, p. 9 | Unverified quality claims, not target values inserted into our experiments |
| 0.036 pJ/pixel, 0.08 ms per 4K frame | IX appendix D/E, Table II | Unverified hardware projections; not measured CPU performance |
| 4K/8K at 120 fps, 4x/8x super-resolution, zero blur | IX appendix C-E | Not implemented or independently established |
| 1D SRAM addressing from arbitrary high-dimensional states | VIII IV; IX standalone V | Not established by this software implementation |

## Numerical and implementation checks

These checks concern the displayed equations; they are not a complete review of every theoretical claim.

- For a contraction bound `q = 63/64`, `q^6` is approximately 0.91. The bound alone guarantees only about a 9% reduction after six steps. About 439 steps are needed for the *bound* to fall below 0.001 of initial error. A particular operator might converge faster, but its definition and stronger evidence would be needed to justify the 4-6 iteration assertion or a probability greater than 0.999. A norm bound is not a success probability.
- Appendix C Eq. (C1) uses phases `exp(i*2*pi*k/p1)` and `exp(-i*2*pi*k/p2)` for a finite sum of length N. Coprimality of the denominators alone does not make that finite sum exactly zero for all prime pairs and N. `scripts/audit_claims.py` records a numerical counterexample for N=1024, p1=3, p2=5. This differs from the usual orthogonal N-point DFT basis `exp(i*2*pi*m*k/N)`.
- 3840*2160 pixels / 0.00008 seconds is 103.68 billion pixels/s. A literal single-lane one-pixel-per-clock interpretation would require 103.68 GHz. Parallelism could change that interpretation, but the reviewed materials do not specify the required lane count, clock, or physical implementation. A 120 fps stream has a separate 8.333 ms frame interval.
- The paper's 2 KiB LUT is 1024 scalar 16-bit sine values. Fairly reconstructing a complex phasor requires both sine and cosine: this software stores 4 KiB at N=1024 or 8 KiB at N=2048. A scalar N=2048 table is 4 KiB. No arbitrary high-dimensional function is compressed into these small tables.
- Mapping a real amplitude through Arg discards amplitude information. The demonstrated identity is restricted to unit-magnitude complex signals; it is not a replacement for arbitrary multiplication, accumulation, neural inference, or general computation.

## Implemented versus experimental

**Direct arithmetic reproduction:** modular addition, floor quantization, scalar signed-Q15 sine LUT, optional paired cosine/sine reconstruction, requested rollover examples, and exhaustive modular-addition tests.

**Experimental image processing:** local Wiener shrinkage (Plane), guided smoothing (Line), and 10-bit scalar intensity quantization (Point). These design choices borrow only the staged vocabulary. They do not implement entropy absorption into delta=1/64, prime-orbit filtering, Dirac distributions, Banach sub-pixel recovery, or the unified master equation. Intensity quantization is clipped and does not wrap bright intensities into dark values.

**Not measured:** silicon energy, CMOS area, SRAM access energy, FO4 depth, PIM throughput, device temperature, optical behavior, or hardware frame latency. CPU timing cannot validate those quantities.
