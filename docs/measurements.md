# Independently measured results

## NumPy CPU run

12th Gen Intel(R) Core(TM) i5-12400; Python 3.12.10; NumPy 2.5.4. Two warm-ups and seven randomized repetitions. The supplied NumPy measurements remain the valid pre-redesign run; they were reviewed and preserved rather than presented as newly collected. Expanded image and native runs are new.

| N | Method | Mean ms | Median ms | Sample SD ms | M products/s | Input MiB | Incremental traced peak MiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10000 | FP32 kernel | 0.00406 | 0.00430 | 0.00080 | 2325.58 | 0.15 | 0.08 |
| 10000 | FP32 encode pair | 0.47831 | 0.44730 | 0.08443 | 22.36 | 0.15 | 0.38 |
| 10000 | FP32 end-to-end | 0.45663 | 0.45180 | 0.00993 | 22.13 | 0.15 | 0.38 |
| 10000 | Z1024 add | 0.00901 | 0.00900 | 0.00027 | 1111.11 | 0.04 | 0.04 |
| 10000 | Z1024 LUT decode | 0.10631 | 0.10580 | 0.00254 | 94.52 | 0.02 | 0.29 |
| 10000 | Z1024 encoded-to-complex | 0.11620 | 0.11490 | 0.00629 | 87.03 | 0.04 | 0.31 |
| 10000 | Z1024 quantize pair | 0.27937 | 0.27990 | 0.00187 | 35.73 | 0.15 | 0.17 |
| 10000 | Z1024 end-to-end | 0.39537 | 0.39430 | 0.00362 | 25.36 | 0.16 | 0.35 |
| 10000 | Z2048 add | 0.00896 | 0.00880 | 0.00028 | 1136.36 | 0.04 | 0.04 |
| 10000 | Z2048 LUT decode | 0.10564 | 0.10470 | 0.00488 | 95.51 | 0.03 | 0.29 |
| 10000 | Z2048 encoded-to-complex | 0.11440 | 0.11430 | 0.00197 | 87.49 | 0.05 | 0.31 |
| 10000 | Z2048 quantize pair | 0.27827 | 0.27860 | 0.00285 | 35.89 | 0.15 | 0.17 |
| 10000 | Z2048 end-to-end | 0.39624 | 0.39430 | 0.00838 | 25.36 | 0.16 | 0.35 |
| 100000 | FP32 kernel | 0.21949 | 0.17020 | 0.13869 | 587.54 | 1.53 | 0.76 |
| 100000 | FP32 encode pair | 5.89793 | 5.91490 | 0.36421 | 16.91 | 1.53 | 3.82 |
| 100000 | FP32 end-to-end | 6.00117 | 5.82980 | 0.33133 | 17.15 | 1.53 | 3.82 |
| 100000 | Z1024 add | 0.11309 | 0.09350 | 0.05381 | 1069.52 | 0.38 | 0.38 |
| 100000 | Z1024 LUT decode | 1.44563 | 1.43170 | 0.13070 | 69.85 | 0.19 | 2.35 |
| 100000 | Z1024 encoded-to-complex | 1.54691 | 1.54340 | 0.12994 | 64.79 | 0.39 | 2.54 |
| 100000 | Z1024 quantize pair | 3.79090 | 3.40960 | 1.16479 | 29.33 | 1.53 | 1.72 |
| 100000 | Z1024 end-to-end | 5.09073 | 5.01430 | 0.22732 | 19.94 | 1.53 | 2.93 |
| 100000 | Z2048 add | 0.11223 | 0.12010 | 0.02636 | 832.64 | 0.38 | 0.38 |
| 100000 | Z2048 LUT decode | 1.44497 | 1.42470 | 0.14736 | 70.19 | 0.20 | 2.35 |
| 100000 | Z2048 encoded-to-complex | 1.47780 | 1.46240 | 0.06408 | 68.38 | 0.39 | 2.54 |
| 100000 | Z2048 quantize pair | 3.50067 | 3.42060 | 0.30008 | 29.23 | 1.53 | 1.72 |
| 100000 | Z2048 end-to-end | 4.85726 | 4.81020 | 0.24106 | 20.79 | 1.53 | 2.93 |
| 1000000 | FP32 kernel | 2.93373 | 2.98290 | 0.59115 | 335.24 | 15.26 | 7.63 |
| 1000000 | FP32 encode pair | 74.25701 | 75.32440 | 9.06308 | 13.28 | 15.26 | 38.15 |
| 1000000 | FP32 end-to-end | 77.15829 | 76.40700 | 4.80624 | 13.09 | 15.26 | 38.15 |
| 1000000 | Z1024 add | 1.51769 | 1.40010 | 0.31045 | 714.23 | 3.81 | 3.82 |
| 1000000 | Z1024 LUT decode | 20.58553 | 21.31370 | 2.00738 | 46.92 | 1.91 | 22.95 |
| 1000000 | Z1024 encoded-to-complex | 23.35549 | 22.55630 | 3.04271 | 44.33 | 3.82 | 24.86 |
| 1000000 | Z1024 quantize pair | 45.08384 | 45.49810 | 4.13966 | 21.98 | 15.26 | 17.17 |
| 1000000 | Z1024 end-to-end | 69.32769 | 71.14940 | 4.09750 | 14.05 | 15.26 | 28.68 |
| 1000000 | Z2048 add | 1.45509 | 1.45740 | 0.25162 | 686.15 | 3.81 | 3.82 |
| 1000000 | Z2048 LUT decode | 22.77114 | 20.73700 | 5.10853 | 48.22 | 1.92 | 22.95 |
| 1000000 | Z2048 encoded-to-complex | 26.61413 | 25.91680 | 4.36240 | 38.59 | 3.82 | 24.86 |
| 1000000 | Z2048 quantize pair | 44.95447 | 44.25710 | 5.50422 | 22.60 | 15.26 | 17.17 |
| 1000000 | Z2048 end-to-end | 73.82860 | 72.56190 | 8.85684 | 13.78 | 15.27 | 28.68 |
| 10000000 | FP32 kernel | 26.77627 | 26.70750 | 2.30600 | 374.43 | 152.59 | 76.30 |
| 10000000 | FP32 encode pair | 704.75901 | 696.11940 | 27.27654 | 14.37 | 152.59 | 381.47 |
| 10000000 | FP32 end-to-end | 750.42900 | 765.73460 | 33.71449 | 13.06 | 152.59 | 381.47 |
| 10000000 | Z1024 add | 16.00951 | 15.85100 | 3.31129 | 630.88 | 38.15 | 38.15 |
| 10000000 | Z1024 LUT decode | 211.03826 | 211.15100 | 7.97420 | 47.36 | 19.08 | 228.95 |
| 10000000 | Z1024 encoded-to-complex | 235.90391 | 231.03920 | 13.72172 | 43.28 | 38.15 | 248.02 |
| 10000000 | Z1024 quantize pair | 468.24160 | 455.25610 | 36.04899 | 21.97 | 152.59 | 171.66 |
| 10000000 | Z1024 end-to-end | 682.66819 | 683.48610 | 23.21639 | 14.63 | 152.59 | 286.17 |
| 10000000 | Z2048 add | 17.41169 | 15.06120 | 4.37270 | 663.96 | 38.15 | 38.15 |
| 10000000 | Z2048 LUT decode | 206.55809 | 200.71780 | 13.23118 | 49.82 | 19.08 | 228.95 |
| 10000000 | Z2048 encoded-to-complex | 232.94967 | 223.76640 | 21.29866 | 44.69 | 38.15 | 248.02 |
| 10000000 | Z2048 quantize pair | 441.31321 | 441.28300 | 19.94222 | 22.66 | 152.59 | 171.66 |
| 10000000 | Z2048 end-to-end | 692.56917 | 695.40450 | 43.26069 | 14.38 | 152.60 | 286.17 |

Integer kernels output indices; FP32 outputs complex values. See encoded-to-complex rows for the same output representation. Full end-to-end paths use identical raw angle inputs and complex64 outputs, with quantization error in the ring branch. Memory is scoped input storage and incremental traced allocation, not full-machine peak or physical SRAM. Raw repetitions: [NumPy samples](../results/timing_samples.csv).

## Numerical error

| N | Method | Samples | Angular RMSE rad | Max angular error rad |
| --- | --- | --- | --- | --- |
| 10000 | FP32 | 10000 | 2.330944061799545e-08 | 1.0927007264878651e-07 |
| 10000 | Z1024 | 10000 | 0.006611315813719158 | 0.01225059773714726 |
| 10000 | Z2048 | 10000 | 0.003320339773795926 | 0.006119346454550454 |
| 100000 | FP32 | 100000 | 2.3266001264757997e-08 | 1.0272103380492667e-07 |
| 100000 | Z1024 | 100000 | 0.006624161270975936 | 0.012263047129263509 |
| 100000 | Z2048 | 100000 | 0.003316430413049717 | 0.006133332291629282 |
| 1000000 | FP32 | 200000 | 2.316312901139463e-08 | 1.1371353117930782e-07 |
| 1000000 | Z1024 | 200000 | 0.006631787359883934 | 0.012264052100586072 |
| 1000000 | Z2048 | 200000 | 0.0033153236583462983 | 0.0061484611573381755 |
| 10000000 | FP32 | 200000 | 2.3132285332914322e-08 | 1.0463748643271359e-07 |
| 10000000 | Z1024 | 200000 | 0.0066300486927239844 | 0.012264865341977703 |
| 10000000 | Z2048 | 200000 | 0.0033097582135037866 | 0.006137186836901893 |

## Separate fused, preallocated C++ run

| N | Method | Median ms | Sample SD ms | M products/s |
| --- | --- | --- | --- | --- |
| 10000 | FP32 kernel | 0.01220 | 0.00843 | 819.67 |
| 10000 | FP32 end-to-end | 0.32070 | 0.20740 | 31.18 |
| 10000 | Z1024 add | 0.00090 | 0.00026 | 11111.11 |
| 10000 | Z1024 encoded-to-complex | 0.02040 | 0.00465 | 490.20 |
| 10000 | Z1024 end-to-end | 0.03630 | 0.01410 | 275.48 |
| 10000 | Z2048 add | 0.00100 | 0.00074 | 10000.00 |
| 10000 | Z2048 encoded-to-complex | 0.02060 | 0.00252 | 485.44 |
| 10000 | Z2048 end-to-end | 0.03640 | 0.01190 | 274.73 |
| 100000 | FP32 kernel | 0.12010 | 0.00721 | 832.64 |
| 100000 | FP32 end-to-end | 3.29690 | 0.12209 | 30.33 |
| 100000 | Z1024 add | 0.00970 | 0.00167 | 10309.28 |
| 100000 | Z1024 encoded-to-complex | 0.18810 | 0.00917 | 531.63 |
| 100000 | Z1024 end-to-end | 0.36920 | 0.01416 | 270.86 |
| 100000 | Z2048 add | 0.01090 | 0.00129 | 9174.31 |
| 100000 | Z2048 encoded-to-complex | 0.18910 | 0.00902 | 528.82 |
| 100000 | Z2048 end-to-end | 0.37040 | 0.01191 | 269.98 |
| 1000000 | FP32 kernel | 1.42070 | 0.15166 | 703.88 |
| 1000000 | FP32 end-to-end | 33.01190 | 0.89841 | 30.29 |
| 1000000 | Z1024 add | 0.39610 | 0.17883 | 2524.61 |
| 1000000 | Z1024 encoded-to-complex | 1.98930 | 0.55083 | 502.69 |
| 1000000 | Z1024 end-to-end | 3.53670 | 0.23524 | 282.75 |
| 1000000 | Z2048 add | 0.34410 | 0.10036 | 2906.13 |
| 1000000 | Z2048 encoded-to-complex | 1.90210 | 0.17269 | 525.73 |
| 1000000 | Z2048 end-to-end | 3.68650 | 1.09872 | 271.26 |
| 10000000 | FP32 kernel | 19.95700 | 2.44164 | 501.08 |
| 10000000 | FP32 end-to-end | 375.66010 | 26.18833 | 26.62 |
| 10000000 | Z1024 add | 3.93450 | 0.62336 | 2541.62 |
| 10000000 | Z1024 encoded-to-complex | 22.98880 | 2.31518 | 434.99 |
| 10000000 | Z1024 end-to-end | 41.99760 | 2.73160 | 238.11 |
| 10000000 | Z2048 add | 4.48350 | 0.69459 | 2230.40 |
| 10000000 | Z2048 encoded-to-complex | 20.27880 | 1.66278 | 493.13 |
| 10000000 | Z2048 end-to-end | 39.25910 | 6.62468 | 254.72 |

Native inputs differ from NumPy. Fusion and preallocation differ too. This is not an isolated language-speed comparison. [Methodology and reproduction](native_benchmark.md), [compiler environment](../results/native_environment.json), [raw native samples](../results/native_samples.csv), [native errors](../results/native_accuracy.csv).

## Expanded 54-case image study

| Method | Mean PSNR (dB) | Mean SSIM | Mean edge score | Mean timing median (ms) |
| --- | --- | --- | --- | --- |
| Gaussian | 25.8461 | 0.7222 | 0.6989 | 0.3751 |
| Bilateral | 34.1422 | 0.8208 | 0.8965 | 5.2794 |
| Median | 26.1502 | 0.5921 | 0.8089 | 0.3220 |
| Legacy V1 | 33.9992 | 0.9271 | 0.8658 | 12.4102 |
| Prototype V2 | 32.6861 | 0.8617 | 0.8795 | 6.0816 |

## Independently timed ablations

| Full callable | Mean PSNR dB | Mean SSIM | Mean edge score | Mean timing median ms |
| --- | --- | --- | --- | --- |
| Local mean | 24.00577 | 0.71238 | 0.60471 | 0.74805 |
| Wiener + guided float | 34.00073 | 0.92719 | 0.86577 | 11.01681 |
| Wiener float | 32.68706 | 0.86174 | 0.87945 | 4.60368 |

All aggregate quality is arithmetic mean of per-case quality; time is the mean of per-case medians. It is not pooled-MSE PSNR or a pooled timing median. Full raw quality, time dispersion and seed-specific results are retained in [expanded CSV](../results/expanded_noise.csv), [expanded timing samples](../results/expanded_noise_samples.csv), [ablation CSV](../results/noise_ablation.csv), and [ablation timing samples](../results/noise_ablation_samples.csv). [Study interpretation](visual_study.md).

## Final native control audit

| Native path / 10M products | Median ms | Sample SD ms | M products/s | Angular RMSE rad |
| --- | --- | --- | --- | --- |
| FP32 four-trig product | 330.396 | 21.774 | 30.27 | 2.571e-08 |
| FP32 summed-angle trig | 195.607 | 19.642 | 51.12 | 1.188e-08 |
| Z1024 Q15 end-to-end | 36.952 | 4.425 | 270.62 | 6.617e-03 |
| Z2048 Q15 end-to-end | 33.259 | 2.304 | 300.67 | 3.311e-03 |
| Z2048 float LUT control | 20.095 | 2.880 | 497.63 | 3.311e-03 |

This is a separate nine-repeat run. Do not merge it with the earlier seven-repeat native results above. [Scope, optimized control, compiler and cache audit](native_audit.md).
