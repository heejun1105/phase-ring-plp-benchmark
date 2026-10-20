// A controlled CPU follow-up. Original native results are never overwritten.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using C = std::complex<float>;
struct Q15 { int16_t re, im; };
constexpr double tau = 6.283185307179586476925286766559;
volatile double checksum_sink = 0;
#if defined(__GNUC__) || defined(__clang__)
#define AUDIT_NOINLINE __attribute__((noinline))
#else
#define AUDIT_NOINLINE __declspec(noinline)
#endif

inline uint16_t quant(double x, int n) {
    return uint16_t(int(std::floor(x * n / tau))) & uint16_t(n - 1);
}
inline C decode(Q15 x) {
    return C(float(x.re) / 32767, float(x.im) / 32767);
}

// Identical operands and complex<float> output for all five timed paths.
// Separate symbols make loop-vectorization and call inspection reproducible.
extern "C" AUDIT_NOINLINE void audit_fp32_product(const double* a, const double* b, C* out, size_t count) {
    for (size_t i = 0; i < count; ++i)
        out[i] = C(std::cos(a[i]), std::sin(a[i])) * C(std::cos(b[i]), std::sin(b[i]));
}
extern "C" AUDIT_NOINLINE void audit_fp32_sum(const double* a, const double* b, C* out, size_t count) {
    for (size_t i = 0; i < count; ++i) {
        const double angle = a[i] + b[i];
        out[i] = C(std::cos(angle), std::sin(angle));
    }
}
extern "C" AUDIT_NOINLINE void audit_z1024(const double* a, const double* b, C* out, size_t count, const Q15* lut) {
    for (size_t i = 0; i < count; ++i)
        out[i] = decode(lut[(quant(a[i], 1024) + quant(b[i], 1024)) & 1023]);
}
extern "C" AUDIT_NOINLINE void audit_z2048(const double* a, const double* b, C* out, size_t count, const Q15* lut) {
    for (size_t i = 0; i < count; ++i)
        out[i] = decode(lut[(quant(a[i], 2048) + quant(b[i], 2048)) & 2047]);
}
extern "C" AUDIT_NOINLINE void audit_float_lut(const double* a, const double* b, C* out, size_t count, const C* lut) {
    for (size_t i = 0; i < count; ++i)
        out[i] = lut[(quant(a[i], 2048) + quant(b[i], 2048)) & 2047];
}

int main(int argc, char** argv) {
    const std::string folder = argc > 1 ? argv[1] : "results";
    const int repeats = argc > 2 ? std::stoi(argv[2]) : 9;
    if (repeats < 7 || repeats % 2 == 0) throw std::runtime_error("Use an odd repetition count of at least seven.");
    std::ofstream raw(folder + "/native_audit_samples.csv"), summary(folder + "/native_audit_benchmark.csv"),
        accuracy(folder + "/native_audit_accuracy.csv"), inputs(folder + "/native_audit_inputs.csv");
    raw << "n,method,repeat,elapsed_ms\n";
    summary << "n,method,mean_ms,median_ms,std_ms,min_ms,max_ms,repeats,warmups,ops_per_sec\n";
    accuracy << "n,method,evaluated_samples,angular_rmse_rad,max_angular_error_rad,complex_rmse,max_complex_error,max_amplitude_error\n";
    inputs << "n,seed,sum_a,sum_b,sum_squares_a,sum_squares_b\n";
    raw << std::setprecision(17); summary << std::setprecision(17);
    accuracy << std::setprecision(17); inputs << std::setprecision(17);

    const std::vector<int> sizes = argc > 3 ? std::vector<int>{std::stoi(argv[3])} : std::vector<int>{10000, 100000, 1000000, 10000000};
    for (const int size : sizes) {
        if (size <= 0) throw std::runtime_error("Size must be positive.");
        std::mt19937 gen(20261020);
        std::uniform_real_distribution<double> dist(-tau / 2, tau / 2);
        std::vector<double> a(size), b(size);
        std::vector<C> out(size), float_lut(2048);
        std::vector<Q15> lut1024(1024), lut2048(2048);
        for (int n : {1024, 2048}) {
            auto& lut = n == 1024 ? lut1024 : lut2048;
            for (int k = 0; k < n; ++k)
                lut[k] = Q15{int16_t(std::cos(k * tau / n) * 32767), int16_t(std::sin(k * tau / n) * 32767)};
        }
        for (int k = 0; k < 2048; ++k)
            float_lut[k] = C(std::cos(k * tau / 2048), std::sin(k * tau / 2048));
        double sa = 0, sb = 0, ssa = 0, ssb = 0;
        for (int i = 0; i < size; ++i) {
            a[i] = dist(gen); b[i] = dist(gen);
            sa += a[i]; sb += b[i]; ssa += a[i] * a[i]; ssb += b[i] * b[i];
        }
        inputs << size << ",20261020," << sa << ',' << sb << ',' << ssa << ',' << ssb << '\n';
        struct Task { std::string name; std::function<void()> fn; std::vector<double> samples; };
        std::vector<Task> tasks;
        tasks.push_back({"FP32 four-trig product", [&] { audit_fp32_product(a.data(), b.data(), out.data(), size); }, {}});
        tasks.push_back({"FP32 summed-angle trig", [&] { audit_fp32_sum(a.data(), b.data(), out.data(), size); }, {}});
        tasks.push_back({"Z1024 Q15 end-to-end", [&] { audit_z1024(a.data(), b.data(), out.data(), size, lut1024.data()); }, {}});
        tasks.push_back({"Z2048 Q15 end-to-end", [&] { audit_z2048(a.data(), b.data(), out.data(), size, lut2048.data()); }, {}});
        tasks.push_back({"Z2048 float LUT control", [&] { audit_float_lut(a.data(), b.data(), out.data(), size, float_lut.data()); }, {}});
        auto consume = [&] {
            double sum = 0;
            for (const auto v : out) sum += v.real() + v.imag();
            checksum_sink = checksum_sink + sum;
        };
        for (auto& task : tasks)
            for (int warm = 0; warm < 2; ++warm) { task.fn(); consume(); }
        std::vector<int> order(tasks.size());
        std::iota(order.begin(), order.end(), 0);
        for (int repeat = 0; repeat < repeats; ++repeat) {
            std::shuffle(order.begin(), order.end(), gen);
            for (const int k : order) {
                auto& task = tasks[k];
                const auto start = std::chrono::steady_clock::now();
                task.fn();
                const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
                task.samples.push_back(ms);
                raw << size << ',' << task.name << ',' << repeat << ',' << ms << '\n';
                consume();
            }
        }
        for (auto& task : tasks) {
            auto v = task.samples;
            std::sort(v.begin(), v.end());
            const double mean = std::accumulate(v.begin(), v.end(), 0.0) / v.size();
            double ss = 0;
            for (const auto z : v) ss += (z - mean) * (z - mean);
            const double median = v[v.size() / 2];
            summary << size << ',' << task.name << ',' << mean << ',' << median << ',' << std::sqrt(ss / (v.size() - 1))
                << ',' << v.front() << ',' << v.back() << ',' << repeats << ",2," << size / (median / 1000) << '\n';
            task.fn(); consume();
            double angular_ss = 0, angular_max = 0, complex_ss = 0, complex_max = 0, amplitude_max = 0;
            const int count = std::min(size, 200000);
            for (int i = 0; i < count; ++i) {
                const double target = a[i] + b[i];
                const double re = out[i].real(), im = out[i].imag();
                const double angular = std::abs(std::remainder(std::atan2(im, re) - target, tau));
                const double complex_error = std::hypot(re - std::cos(target), im - std::sin(target));
                angular_ss += angular * angular; angular_max = std::max(angular_max, angular);
                complex_ss += complex_error * complex_error; complex_max = std::max(complex_max, complex_error);
                amplitude_max = std::max(amplitude_max, std::abs(std::hypot(re, im) - 1));
            }
            accuracy << size << ',' << task.name << ',' << count << ',' << std::sqrt(angular_ss / count) << ',' << angular_max
                << ',' << std::sqrt(complex_ss / count) << ',' << complex_max << ',' << amplitude_max << '\n';
        }
        std::cout << "Native CPU audit complete: " << size << std::endl;
    }
    std::cout << "Checksum: " << checksum_sink << std::endl;
    return raw && summary && accuracy && inputs ? 0 : 1;
}
