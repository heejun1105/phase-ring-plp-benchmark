# Native CPU audit and optimized control

The earlier 10M native result (375.6601 ms versus 41.9976/39.2591 ms) is retained unchanged. The follow-up uses a new source file and new result files. Its first run measures 330.3962 ms for the four-trig complex product and 36.9522/33.2588 ms for the two Q15 phase paths: **8.94x/9.93x shorter runtime for this specific baseline and workload**. These are CPU observations, not general FP32 or PIM hardware speedups.

An optimized, mathematically equivalent unit-phasor control adds the two angles first and calls sine/cosine only once each. It takes 195.6071 ms, reducing the Q15 advantages to **5.29x/5.88x**. This control also has a smaller numerical error than the four-trig path. The reduction shows that the headline depends strongly on redundant trigonometric work in the chosen baseline.

## Inputs, outputs and timed work

All five methods read the same two preallocated **float64 angle arrays** and write the same preallocated **complex<float> output array**. Thus the name FP32 describes the complex output/arithmetic, not an all-float32 input or trigonometric pipeline. The sine/cosine calls use double inputs and double results before conversion. No method is a general complex multiplication with arbitrary magnitudes.

| Method | Work inside the timed loop | Lookup table |
|---|---|---|
| FP32 four-trig product | Two double-input sine/cosine pairs, conversion to two complex<float> phasors, complex multiplication, output write | None |
| FP32 summed-angle trig | Double angle addition, one double-input sine/cosine pair, conversion to complex<float>, output write | None |
| Z1024 / Z2048 Q15 end-to-end | Two floor quantizations, masked index addition, paired int16 Q15 lookup, integer-to-float conversion and /32767 scaling, output write | 4 / 8 KiB |
| Z2048 float LUT control | The same two floor quantizations and masked addition as Z2048, complex<float> lookup and output write | 16 KiB |

The float LUT control is a **quantized phase-index algorithm**. It is not an unquantized FP32 baseline. It isolates a representation/restoration choice: the larger float table avoids the Q15 conversion/scaling and amplitude quantization, while retaining essentially the same phase error. Table construction and all allocations are outside timing for every method. This is a steady-state throughput experiment; one-shot table setup costs are not reported.

The phase mapping is `floor(angle * N / tau)` followed by the mask `N-1`. Both inputs are quantized separately before addition. Two floor errors can accumulate, so the product angular error can approach two phase bins; integer wrap itself is exact. Q15 entry truncation adds a smaller output error. The output representation is shared, while accuracy is deliberately different.

## Supplied 10M measurements

Two warm-ups and nine randomized repetitions use `steady_clock` for each method at N=10K, 100K, 1M and 10M. Throughput counts one output unit-phasor product per item. Standard deviation below is the sample standard deviation of nine wall-clock durations, not an uncertainty bound on the ratio.

| Method | Median ms | Std ms | Million outputs/s | Four-trig time / method time |
|---|---:|---:|---:|---:|
| FP32 four-trig product | 330.3962 | 21.7743 | 30.27 | 1.00x |
| FP32 summed-angle trig | 195.6071 | 19.6424 | 51.12 | 1.69x |
| Z1024 Q15 end-to-end | 36.9522 | 4.4250 | 270.62 | 8.94x |
| Z2048 Q15 end-to-end | 33.2588 | 2.3041 | 300.67 | 9.93x |
| Z2048 float LUT control | 20.0952 | 2.8797 | 497.63 | 16.44x |

The headline compares the first, third and fourth rows from this one run. Do not take a numerator from the older run and a denominator from this run. The float LUT control is kept out of the headline because it tests a different storage/restoration policy.

## Accuracy is part of the result

The first min(N,200000) pairs are compared against double-precision cosine/sine of the summed angle, outside timing. At 10M this is a 200K-prefix accuracy check, not an exhaustive numerical comparison of all 10M outputs. Complex RMSE is `sqrt(mean(abs(output-reference)**2))`; angular errors use a wrapped difference in radians.

| Method | Angular RMSE rad | Angular RMSE deg | Complex RMSE | Max amplitude error |
|---|---:|---:|---:|---:|
| FP32 four-trig product | 2.5712e-8 | 1.4732e-6 | 4.2970e-8 | 1.3764e-7 |
| FP32 summed-angle trig | 1.1882e-8 | 6.8081e-7 | 2.0597e-8 | 4.1856e-8 |
| Z1024 Q15 end-to-end | 0.00661736 | 0.379147 | 0.00661731 | 3.8654e-5 |
| Z2048 Q15 end-to-end | 0.00331063 | 0.189685 | 0.00331066 | 3.9957e-5 |
| Z2048 float LUT control | 0.00331065 | 0.189686 | 0.00331065 | 3.6762e-8 |

## Compiler, SIMD and cache audit

The supplied build uses the optional Zig driver's Clang 21.1.0 backend with `-O3 -std=c++17`, no `-ffast-math` and no explicit `-march=native`. The driver still enables host features including AVX/AVX2 and SSE4.1; the full compiler target/features are recorded in the environment JSON. Absence of the explicit flag must not be read as a generic CPU target guarantee.

Compiler remarks report that none of the five timed loops was auto-vectorized across input items. Assembly shows scalar `cos` and `sin` calls in the two trigonometric paths; this build did not fuse them into a `sincos` call. The four-trig function also contains a `__mulsc3` fallback call site for complex arithmetic. A static call site does not establish how often that fallback executes. The phase paths have no library calls in their timed function bodies. They use packed `vmulpd`/`vdivpd` operations within an item, which is distinct from vectorizing multiple output items. No FMA instructions were found in these function bodies.

The Q15 and float table paths benefit from avoiding per-item transcendental calls and using small tables. The float LUT control also avoids Q15 decoding. The C++ loops fuse the operations and write one output array; the NumPy experiment uses several array expressions and intermediate allocations. These observations explain plausible causes, but the experiments do not separately measure the cost of language, cache misses, allocation, or every primitive. No hardware performance counters or bandwidth/IPC measurements were collected.

Full-output checksums are consumed outside timing after every warm-up and repetition to keep writes observable. The checksum pass affects cache state; methods do not start from an explicitly flushed cache. The 10M input/output arrays exceed the small lookup-table footprint by orders of magnitude. There is one worker thread, but no process affinity or CPU frequency lock. Windows scheduling and boost can change timings.

## Separate stability check

A second 10M run is retained in its own directory, with the same source, toolchain, nine repetitions, input checksums and numerical outputs. Its medians are 320.5205 ms (four-trig), 175.4282 ms (summed-angle), 33.3384 ms (Z1024), 34.1241 ms (Z2048), and 19.4936 ms (float LUT control). The largest median change is 10.32%; the two Q15 paths reverse order. Thus this machine/run does not establish a robust performance ranking between N=1024 and N=2048. Their accuracy difference remains clear.

The follow-up does not silently replace the original measurements. SHA256 hashes of all four original native result files are recorded and checked before/after each audit run. The original source and original benchmark driver are unchanged.

## Reproduce and inspect

```bash
# Optional Zig compiler, or use an existing clang++/g++:
python -m pip install -r requirements-native.txt
python scripts/run_native_audit.py

# Independent 10M stability check; keep first-run files:
python scripts/run_native_audit.py --size 10000000 --output-dir results/native_audit_repeat
```

[Source](../native/audit_benchmark.cpp), [driver](../scripts/run_native_audit.py), [raw repetitions](../results/native_audit_samples.csv), [summary](../results/native_audit_benchmark.csv), [accuracy](../results/native_audit_accuracy.csv), [input checksums](../results/native_audit_inputs.csv), [environment and original hashes](../results/native_audit_environment.json), [compiler inspection](../results/native_audit_compiler.json), [second-run summary](../results/native_audit_repeat/native_audit_benchmark.csv), [second-run raw repetitions](../results/native_audit_repeat/native_audit_samples.csv).

This audit does not measure SRAM execution, RTL timing, synthesis, energy, area, FO4, or silicon. It does not validate the paper's hardware estimates or its PLP equations. The unit-phasor identity and reduced precision are workload assumptions, not interchangeable definitions of a general FP32 MAC.
