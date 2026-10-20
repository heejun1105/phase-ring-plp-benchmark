"""Reproduce measurements and animations from the repository root."""
import argparse, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--quick',action='store_true',help='Only 10K/100K compute sizes and 3 repeats; noise cases unchanged.')
    p.add_argument('--skip-benchmark',action='store_true',help='Render from existing measured CSV files.')
    p.add_argument('--skip-render',action='store_true')
    a=p.parse_args();os.chdir(ROOT)
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],check=True)
    from src.phase_ring import make_lut
    for n in [1024,2048]:
        values=make_lut(n)[:,1]
        (ROOT/f'hardware/sine_q15_{n}.hex').write_text(''.join(f'{int(x)&65535:04x}\n' for x in values),encoding='ascii')
    if not a.skip_benchmark:
        from src.benchmark.run import main as benchmark
        benchmark(sizes=(10000,100000) if a.quick else (10000,100000,1000000,10000000),repeats=3 if a.quick else 7)
    from scripts.build_report import main as report
    report()
    if not a.skip_render:
        from scripts.render import main as render
        render()
    from scripts.validate import main as validate
    validate(require_media=not a.skip_render)

if __name__=='__main__':main()
