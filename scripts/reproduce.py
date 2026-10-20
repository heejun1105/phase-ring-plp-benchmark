"""Reproduce measurements and animations from the repository root."""
import argparse, os, subprocess, sys,unittest,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--quick',action='store_true',help='Only 10K/100K compute sizes and 3 repeats; noise cases unchanged.')
    p.add_argument('--skip-benchmark',action='store_true',help='Render from existing measured CSV files.')
    p.add_argument('--skip-render',action='store_true')
    p.add_argument('--native',action='store_true',help='Compile and run the optional fused C++ CPU study.')
    p.add_argument('--native-audit',action='store_true',help='Collect the separate optimized-control audit; retain original native results.')
    a=p.parse_args();os.chdir(ROOT)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit('Tests failed; no data or media regenerated.')
    (ROOT/'results/test_results.json').write_text(json.dumps(dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful()),indent=2),encoding='utf-8')
    from src.phase_ring import make_lut
    for n in [1024,2048]:
        values=make_lut(n)[:,1]
        (ROOT/f'hardware/sine_q15_{n}.hex').write_text(''.join(f'{int(x)&65535:04x}\n' for x in values),encoding='ascii')
    if not a.skip_benchmark:
        from src.benchmark.run import main as benchmark
        benchmark(sizes=(10000,100000) if a.quick else (10000,100000,1000000,10000000),repeats=3 if a.quick else 7)
        from src.benchmark.visual_study import main as visual_study
        visual_study(repeats=3 if a.quick else 7)
    if a.native:subprocess.run([sys.executable,'-m','scripts.run_native'],check=True)
    if a.native_audit:subprocess.run([sys.executable,'-m','scripts.run_native_audit'],check=True)
    from scripts.study_figures import main as figures
    figures()
    if not a.skip_render:
        from scripts.visualize_v3 import Study,NAMES,export
        study=Study()
        audited=(ROOT/'results/native_audit_benchmark.csv').exists()
        for name in NAMES:
            if audited and name=='noise_reduction_comparison':continue
            export(name,study)
        if audited:
            from scripts.visualize_v4 import NAMES as revised_names,export as revised_export
            for name in revised_names:revised_export(name)
    from scripts.gallery_report import main as report
    report()
    from scripts.validate_v3 import main as validate
    validate(require_media=not a.skip_render)

if __name__=='__main__':main()
