# Measured result tables

| Phase products | FP32 complex kernel (ms) | Z1024 add (ms) | Z2048 add (ms) |
| --- | --- | --- | --- |
| 10,000 | 0.0048 | 0.0091 | 0.0091 |
| 100,000 | 0.1729 | 0.1061 | 0.1263 |
| 1,000,000 | 2.4630 | 1.7479 | 1.5031 |
| 10,000,000 | 26.5469 | 16.9446 | 13.8621 |

| Pipeline at 10,000,000 products | Median (ms) | Throughput (M phase products/s) |
| --- | --- | --- |
| FP32 kernel | 26.547 | 376.69 |
| Z1024 encoded-to-complex | 226.846 | 44.08 |
| Z2048 encoded-to-complex | 244.830 | 40.84 |
| FP32 end-to-end | 739.620 | 13.52 |
| Z1024 end-to-end | 696.301 | 14.36 |
| Z2048 end-to-end | 656.796 | 15.23 |

| Method | Angular RMSE (rad) | Max angular error (rad) | Complex RMSE |
| --- | --- | --- | --- |
| FP32 | 2.313229e-08 | 1.046375e-07 | 3.915263e-08 |
| Z1024 | 0.006630049 | 0.01226487 | 0.006629999 |
| Z2048 | 0.003309758 | 0.006137187 | 0.003309788 |

| Method | Mean (ms) | Median (ms) | Sample SD (ms) | Input MiB | Incremental traced allocation peak (MiB) |
| --- | --- | --- | --- | --- | --- |
| FP32 kernel | 26.295 | 26.547 | 2.527 | 152.59 | 76.30 |
| Z1024 add | 16.937 | 16.945 | 4.507 | 38.15 | 38.15 |
| Z2048 add | 15.309 | 13.862 | 2.962 | 38.15 | 38.15 |
| Z1024 encoded-to-complex | 227.031 | 226.846 | 13.249 | 38.15 | 248.02 |
| Z2048 encoded-to-complex | 240.942 | 244.830 | 14.625 | 38.15 | 248.02 |
| FP32 end-to-end | 761.184 | 739.620 | 48.599 | 152.59 | 381.47 |
| Z1024 end-to-end | 714.225 | 696.301 | 84.541 | 152.59 | 286.17 |
| Z2048 end-to-end | 676.444 | 656.796 | 44.818 | 152.60 | 286.17 |

| Method | PSNR (dB) | SSIM | Edge score | Mean of timing medians (ms) |
| --- | --- | --- | --- | --- |
| Gaussian | 28.576 | 0.7520 | 0.7215 | 0.464 |
| Bilateral | 30.439 | 0.7779 | 0.8232 | 7.146 |
| Median | 28.062 | 0.6547 | 0.7870 | 0.368 |
| PLP-Inspired Experimental Prototype | 30.629 | 0.8394 | 0.8213 | 14.441 |
| Noisy input | 24.637 | 0.4559 | 0.8615 | 0.289 |
