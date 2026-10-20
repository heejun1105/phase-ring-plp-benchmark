# Optional fused C++ CPU study

`native/benchmark.cpp` compares the same unit-phasor workload within a separately controlled native experiment. All native paths use preallocated inputs and outputs, and no allocation is timed. FP32 uses `std::complex<float>`. Phase indices are uint16 containers with a 10/11-bit mask. The LUT stores paired int16 signed-Q15 sine/cosine entries (4/8 KiB), matching Python storage. Integer-to-float conversion and scaling to complex output occur inside each timed fused loop; predecoded float tables do not hide restoration cost.

The compiler uses `-O3 -std=c++17`, without `-ffast-math`. A single fused loop implements each path. This allows the compiler to optimize expressions and avoids NumPy's multiple intermediate-array allocations. Thus results explain an implementation choice; they do not isolate the Python interpreter cost or imply that changing language alone produces the measured difference.

For each N=10K/100K/1M/10M, a seeded C++ mt19937 produces uniform float64 angles in [-pi,pi). Each native method sees the same pair of angle arrays. The native dataset differs from the earlier NumPy dataset and standard-library distributions may vary by platform. Two warm-ups and seven randomized repetitions use `steady_clock`. A full-output checksum is consumed outside timing after every call to keep output writes observable; this can affect cache state equally across methods and is disclosed rather than interpreted as hardware behavior.

Three scopes are retained: pre-encoded complex multiplication versus integer-index addition (different output types), encoded-to-complex output (same output representation), and raw angles to complex output (end-to-end). LUT construction is outside steady-state timing for both. Native angular error is independently checked against double-precision summed angles on the first min(N,200000) pairs.

The measured environment and flags are in `results/native_environment.json`. Every timing repetition is in `native_samples.csv`, summaries in `native_benchmark.csv`, and errors in `native_accuracy.csv`. Do not combine native and NumPy timing values into a single speedup table without their different allocation/fusion and input policies.

```bash
# Existing clang++ or g++:
python scripts/run_native.py

# Optional portable compiler driver used for the supplied Windows run:
python -m pip install -r requirements-native.txt
python scripts/run_native.py

# Explicit compiler:
python scripts/run_native.py --compiler /path/to/clang++
```

The supplied native run used the clang backend reported by the optional Zig driver. No compiler binary is vendored. Compilation occurs in a temporary directory. This is a CPU experiment, not RTL simulation, synthesis, in-memory execution, SRAM timing, chip power, area, FO4 or silicon validation.
