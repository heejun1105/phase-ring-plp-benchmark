"""Run separate native controls and preserve every original native measurement."""
from pathlib import Path
import argparse, csv, hashlib, importlib.util, json, os, platform, re, shutil, statistics, subprocess, tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'native/audit_benchmark.cpp'
SYMBOLS = ['audit_fp32_product', 'audit_fp32_sum', 'audit_z1024', 'audit_z2048', 'audit_float_lut']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compiler_command(explicit=None):
    if explicit:
        return [explicit]
    for name in ['clang++', 'g++']:
        executable = shutil.which(name)
        if executable:
            return [executable]
    spec = importlib.util.find_spec('ziglang')
    if spec:
        return [str(Path(spec.origin).parent / ('zig.exe' if platform.system() == 'Windows' else 'zig')), 'c++']
    raise SystemExit('No C++ compiler found; install clang/g++ or requirements-native.txt.')

def inspect_assembly(assembly, diagnostics):
    sections = {}
    for symbol in SYMBOLS:
        match = re.search(r'^' + symbol + r':.*?(?=^\s*\.seh_endproc|^\s*\.size\s+' + symbol + r'|\Z)', assembly, re.M | re.S)
        body = match.group(0) if match else ''
        calls = re.findall(r'^\s*call\s+([^\s;]+)', body, re.M)
        # Packed operations are evidence of instruction use, not proof of across-item vectorization.
        packed = sorted(set(re.findall(r'\bv?(?:addpd|mulpd|divpd|subpd|addps|mulps|divps|subps|andps|orpd|andpd|pand|paddw|movups|movupd|cvtdq2ps)\b', body)))
        fused = sorted(set(re.findall(r'\bv?f(?:madd|msub|nmadd|nmsub)[0-9]*(?:ps|pd|ss|sd)\b', body)))
        sections[symbol] = dict(symbol_found=bool(body), assembly_line_count=len(body.splitlines()),
            call_targets=sorted(set(calls)), call_site_count=len(calls), packed_instructions_observed=packed, fused_instructions_observed=fused,
            interpretation='Packed instructions can combine operands or components within one item; they do not alone establish vectorization across input items.')
    remarks = [line.strip() for line in diagnostics.splitlines() if 'remark:' in line and 'audit_benchmark.cpp:' in line]
    return dict(functions=sections, loop_remarks=remarks,
        scope='Compiler assembly and remarks for this build only. No hardware performance counters or bandwidth/IPC measurement.')

def inspect_compiler_target(compiler, flags):
    probe = subprocess.run(compiler + flags + ['-###', '-c', str(SOURCE)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    def option(name):
        match = re.search(r'"' + re.escape(name) + r'"\s+"([^"]+)"', probe.stdout)
        return match.group(1) if match else 'not reported'
    return dict(triple=option('-triple'), cpu=option('-target-cpu'),
        features=re.findall(r'"-target-feature"\s+"([^"]+)"', probe.stdout),
        interpretation='Compiler-driver defaults are recorded. Absence of an explicit -march=native flag does not imply a portable generic CPU target.')

def validate_data(output):
    with (output / 'native_audit_samples.csv').open(encoding='utf-8') as f:
        raw = list(csv.DictReader(f))
    with (output / 'native_audit_benchmark.csv').open(encoding='utf-8') as f:
        summary = list(csv.DictReader(f))
    for row in summary:
        vals = [float(x['elapsed_ms']) for x in raw if x['n'] == row['n'] and x['method'] == row['method']]
        if len(vals) != int(row['repeats']):
            raise AssertionError('Missing audit samples')
        for key, value in [('mean_ms', statistics.mean(vals)), ('median_ms', statistics.median(vals)), ('std_ms', statistics.stdev(vals))]:
            if abs(float(row[key]) - value) > 1e-9:
                raise AssertionError('Audit aggregate mismatch: ' + key)
    with (output / 'native_audit_accuracy.csv').open(encoding='utf-8') as f:
        accuracy = list(csv.DictReader(f))
    for row in accuracy:
        n = 1024 if '1024' in row['method'] else (2048 if '2048' in row['method'] else 0)
        limit = 2 * 6.283185307179586 / n + 0.0001 if n else 2e-6
        if float(row['max_angular_error_rad']) >= limit:
            raise AssertionError('Audit angular bound: ' + row['method'])
    return dict(summary_rows=len(summary), sample_rows=len(raw), accuracy_rows=len(accuracy), raw_aggregates='passed', angular_bounds='passed')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler')
    parser.add_argument('--repeats', type=int, default=9)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'results')
    parser.add_argument('--size', type=int, help='Optional single size for a separate stability check.')
    args = parser.parse_args()
    if args.repeats < 7 or args.repeats % 2 == 0:
        parser.error('--repeats must be odd and at least seven')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    preserved = {p.name: sha(p) for p in (ROOT / 'results').glob('native_*') if p.is_file() and not p.name.startswith('native_audit_')}
    compiler = compiler_command(args.compiler)
    version = subprocess.check_output(compiler + ['--version'], text=True).splitlines()[0]
    flags = ['-O3', '-std=c++17']
    with tempfile.TemporaryDirectory(prefix='phase-ring-native-audit-') as folder:
        temp = Path(folder)
        executable = temp / ('audit.exe' if platform.system() == 'Windows' else 'audit')
        result = subprocess.run(compiler + flags + [str(SOURCE), '-o', str(executable)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError('C++ audit compilation failed:\n' + result.stdout[-5000:])
        # The executable has no other active worker threads or external process work.
        run_args = [str(executable), str(output), str(args.repeats)]
        if args.size:
            run_args.append(str(args.size))
        subprocess.run(run_args, check=True)
        asm = temp / 'audit.s'
        analysis_flags = flags + ['-S', '-masm=intel']
        if 'clang' in version:
            analysis_flags += ['-Rpass=loop-vectorize', '-Rpass-missed=loop-vectorize', '-Rpass-analysis=loop-vectorize']
        analysis = subprocess.run(compiler + analysis_flags + [str(SOURCE), '-o', str(asm)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        compiler_info = inspect_assembly(asm.read_text(encoding='utf-8'), analysis.stdout) if analysis.returncode == 0 else dict(available=False, reason=analysis.stdout[-1000:])
    for name, digest in preserved.items():
        if sha(ROOT / 'results' / name) != digest:
            raise AssertionError('Original native measurement was changed: ' + name)
    info = dict(compiler=version, flags=flags, compiler_target=inspect_compiler_target(compiler, flags), fast_math=False, march_native_flag=False, threads=1,
        platform=platform.platform(), processor=platform.processor(), logical_cpus=os.cpu_count(),
        measured_at_utc=datetime.fromtimestamp((output / 'native_audit_samples.csv').stat().st_mtime, timezone.utc).isoformat(),
        input='C++ mt19937 seed 20261020; uniform float64 angles [-pi,pi); identical arrays for all five audit paths; generation order matches the original native study on this toolchain',
        output='Every timed path writes a preallocated complex<float> array representing a product of unit phasors; finite-precision errors differ',
        allocation='Input, output and lookup-table allocation and table construction excluded from every timed path',
        lut_storage=dict(z1024_q15_bytes=4096, z2048_q15_bytes=8192, z2048_float_control_bytes=16384,
            q15_restoration='Paired int16 to float conversion and /32767 scaling inside timed loops',
            float_control='Same two floor-quantized input indices as Z2048; float table avoids Q15 amplitude quantization but retains phase quantization'),
        trig='Four-trig path: cos/sin of each double input, cast to complex<float>, complex product. Summed-angle path: one double angle sum, one cos/sin pair, cast to complex<float>. Compiler may combine sin/cos calls.',
        timing='steady_clock; two warmups per path; randomized path order per repetition; full output checksums outside timing after each call',
        cache='No forced cache flush or affinity; sequential full-output checksums affect subsequent cache state; tables fit in small CPU caches. No cache-miss counters collected.',
        affinity='No process affinity or frequency lock; Windows scheduling and CPU boost remain sources of variation',
        accuracy='First min(N,200000) pairs versus double cos/sin of summed angle, outside timing; not all 10M outputs numerically compared',
        original_results_sha256=preserved, source_sha256=sha(SOURCE), validation=validate_data(output),
        limitations='Specific single-thread optimized CPU workload; unit phasors only; not general FP32 multiplication, pure language speed, physical PIM, energy or RTL validation')
    (output / 'native_audit_environment.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    (output / 'native_audit_compiler.json').write_text(json.dumps(compiler_info, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(info['validation']))

if __name__ == '__main__':
    main()
