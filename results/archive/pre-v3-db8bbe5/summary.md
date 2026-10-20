# Measured result tables

| Phase products | FP32 complex kernel (ms) | Z1024 add (ms) | Z2048 add (ms) |
| --- | --- | --- | --- |
| 10,000 | 0.0043 | 0.0090 | 0.0088 |
| 100,000 | 0.1702 | 0.0935 | 0.1201 |
| 1,000,000 | 2.9829 | 1.4001 | 1.4574 |
| 10,000,000 | 26.7075 | 15.8510 | 15.0612 |

| Pipeline at 10,000,000 products | Median (ms) | Throughput (M phase products/s) |
| --- | --- | --- |
| FP32 kernel | 26.707 | 374.43 |
| Z1024 encoded-to-complex | 231.039 | 43.28 |
| Z2048 encoded-to-complex | 223.766 | 44.69 |
| FP32 end-to-end | 765.735 | 13.06 |
| Z1024 end-to-end | 683.486 | 14.63 |
| Z2048 end-to-end | 695.404 | 14.38 |

| Method | Angular RMSE (rad) | Max angular error (rad) | Complex RMSE |
| --- | --- | --- | --- |
| FP32 | 2.313229e-08 | 1.046375e-07 | 3.915263e-08 |
| Z1024 | 0.006630049 | 0.01226487 | 0.006629999 |
| Z2048 | 0.003309758 | 0.006137187 | 0.003309788 |

| Method | Mean (ms) | Median (ms) | Sample SD (ms) | Input MiB | Incremental traced allocation peak (MiB) |
| --- | --- | --- | --- | --- | --- |
| FP32 kernel | 26.776 | 26.707 | 2.306 | 152.59 | 76.30 |
| Z1024 add | 16.010 | 15.851 | 3.311 | 38.15 | 38.15 |
| Z2048 add | 17.412 | 15.061 | 4.373 | 38.15 | 38.15 |
| Z1024 encoded-to-complex | 235.904 | 231.039 | 13.722 | 38.15 | 248.02 |
| Z2048 encoded-to-complex | 232.950 | 223.766 | 21.299 | 38.15 | 248.02 |
| FP32 end-to-end | 750.429 | 765.735 | 33.714 | 152.59 | 381.47 |
| Z1024 end-to-end | 682.668 | 683.486 | 23.216 | 152.59 | 286.17 |
| Z2048 end-to-end | 692.569 | 695.404 | 43.261 | 152.60 | 286.17 |

| Method | PSNR (dB) | SSIM | Edge score | Mean of timing medians (ms) |
| --- | --- | --- | --- | --- |
| Gaussian | 28.576 | 0.7520 | 0.7215 | 0.397 |
| Bilateral | 30.439 | 0.7779 | 0.8232 | 5.424 |
| Median | 28.062 | 0.6547 | 0.7870 | 0.322 |
| PLP-Inspired Experimental Prototype | 30.629 | 0.8394 | 0.8213 | 12.270 |
| Noisy input | 24.637 | 0.4559 | 0.8615 | 0.266 |
