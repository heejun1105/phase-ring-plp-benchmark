# Image-first noise comparison

The revised 15-second `noise_reduction_comparison` uses the existing recorded
arrays and measurements. No filtering algorithm, parameters, noise realization,
CSV measurement, or selected representative case changes.

| Time | Visible evidence |
| --- | --- |
| 0–3.1 s | Enlarged noisy microtext beside the recorded Bilateral output |
| 3.1–6.2 s | The same noisy crop beside the recorded PLP-inspired V2 output |
| 6.2–9.2 s | Synchronized dense-line, object-edge and dark-texture crops |
| 9.2–10.6 s | Absolute pixel-error maps, shared range 0–0.20 |
| 10.6–12 s | Absolute Sobel-magnitude-error maps, shared range 0–1.00 |
| 12–15 s | Large V1/V2 PSNR, SSIM, edge-score and CPU-time comparison |

The first two scenes use a labeled editorial wipe to reveal an already computed
output. The wipe is not an algorithm iteration, a convergence trace, a live
execution, or a claim about intermediate states. The final 0.8-second loop blend
is also editorial.

Both large image panels and the clean reference use the exact same aspect-2
crop and magnification on each frame. Ordinary fixtures use the same grayscale
mapping from [0,1] to [0,255]. The dark-texture scene applies a shared display
gain of 1/0.22 with clipping to every compared image. No method receives
sharpening, local contrast enhancement or an independent normalization. Metrics
always refer to the full original [0,1] image, before cropping or display gain.

Images occupy the first 9.2 seconds. The two later error scenes retain a clean
reference and separately show `abs(noisy - output)` with range 0–0.20. Bright
removed-intensity pixels can include noise and signal; these maps do not by
themselves establish detail preservation. All error-map ranges and color maps
are identical between methods. The small-text example is the predeclared
microtext fixture at sigma 0.06, seed 20261020, with V2-minus-Bilateral PSNR
of -0.273919 dB and gain rank 34/54. It was not selected for a favorable result.

The final comparison states **Faster Processing vs. Noise Removal Quality**.
Across all 54 cases, V1 and V2 respectively have mean PSNR 33.9992 and 32.6861 dB,
SSIM 0.92713 and 0.86169, edge score 0.86578 and 0.87946, and mean of per-case
CPU timing medians 12.4102 and 6.0816 ms. V2's lower time and higher mean edge
score accompany lower mean PSNR and SSIM. The edge score is the custom
clean-edge agreement metric defined in the study methodology, not a standard
perceptual quality score. These CPU measurements provide no PIM energy or
hardware-latency measurement.

Both variants carry this caveat throughout the animation:

> PLP-Inspired Experimental Prototype — Not a Validated Implementation of the Original PLP Equations

The source renderer is [visualize_noise_v4.py](../scripts/visualize_noise_v4.py).
The underlying suite and limitations are documented in
[visual_study.md](visual_study.md); the raw measurements remain
[expanded_noise.csv](../results/expanded_noise.csv), with timing samples in
[expanded_noise_samples.csv](../results/expanded_noise_samples.csv).
