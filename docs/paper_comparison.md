# English original and earlier translation

The English PDF supplied by the owner contains the same Paper VIII and appended
signal/image-processing Paper IX as the earlier Korean reference. The reviewed
equations, code listings and table values agree. The PDFs have different dates,
languages, pagination and bytes, so they should not be described as identical
files or as the same dated edition.

| | English original, now included | Earlier Korean translation, not included |
| --- | --- | --- |
| Printed date | September 16, 2026 | October 1, 2026 |
| Pages | 9 | 9 |
| Paper VIII | Pages 1-5 | Pages 1-5 |
| Appended image-processing IX | Pages 6-9 | Pages 6-9 |
| SHA-256 | `d743c111e16aef248092c8bb077ae6edf79942103f6810c3bc4180e3e57faefc` | `249f651810bce6fab84693dd1049a3a551ab15e0b59893b5cd82a0461171ea41` |

The new file's hash also matches the English comparison edition recorded during
the earlier implementation review. This upload does not introduce a new
algorithm, measurement or a revised mathematical model.

## Content checked

| Material | English pages | Translation pages | Finding |
| --- | --- | --- | --- |
| Quantization and modular phase addition, Eq. (1)-(4) | 1-2 | 1 | Same floor/modulo rules, 1024/2048 moduli and overflow examples |
| PLP master expression, Eq. (5) | 2 | 2 | Same plane/entropy, prime-contour and localization structure |
| Contraction bound, Eq. (6) | 3 | 2 | Same 0.984375 factor and 4-6-iteration claim |
| Architectural limitations and photonic proposals, Eq. (7)-(11) | 3-4 | 2-3 | Same scope and claims |
| Circuit Table I | 4 | 3 | Same area, energy and FO4 values |
| Verilog and Python, Listings 1-2 | 4 | 4 | Same arithmetic, scalar sine table and requested examples |
| Image-processing IX, Eq. (B1)-(B4) | 6-7 | 6-7 | Same three-stage and unified expressions |
| Finite prime sum, Eq. (C1) | 8 | 7 | Same expression; earlier numerical caveat still applies |
| Contraction and modular image path, Eq. (C2), (D1) | 8 | 8 | Same expressions and performance claims |
| Image Table II | 9 | 9 | Same PSNR, SSIM, pixel energy, latency and memory claims |

Table I still gives approximately 270 um², 0.015 pJ/op and 4 FO4 for the phase
adder. Table II still gives 48.6 dB PSNR, 0.993 SSIM, 0.036 pJ/pixel and 0.08 ms
per 4K frame. These are paper claims. They are not the CPU or image-filter
measurements collected in this repository.

All nine pages of both files were extracted and reviewed, with page renderings
used to inspect equations, code and both tables. No change affecting the
implemented phase arithmetic was found. This comparison is a section/equation/
listing/table review, not a certification of every translated sentence. The
English file includes the image-processing IX appendix, not the different
standalone Paper IX previously examined.

## Repository update

The owner requested the English original be added instead of the translation.
The [included PDF](../paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf)
is an unchanged copy of those supplied bytes. The translation is not uploaded.
The [current source manifest](../results/source_manifest.json) makes English the
primary reference; the [prior manifest](../results/archive/source_manifest_viii_ko.json)
preserves the earlier source record. Source-to-code page references now use the
English edition.

The switch of reference does not establish physical PIM performance or a full
PLP denoiser. Existing experiment data, numerical algorithms and videos are
unchanged. [Technical review](paper_review.md) and [implementation mapping](source_alignment.md)
give the limits of the reproduction.
