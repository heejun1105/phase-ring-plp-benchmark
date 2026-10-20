"""Compile and execute the optional native benchmark; never substitute invented results."""
from pathlib import Path
import argparse,importlib.util,json,platform,shutil,subprocess,tempfile,os
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',help='C++ compiler executable; otherwise discover clang++, g++ or optional ziglang.')
    a=p.parse_args();compiler=[a.compiler] if a.compiler else None
    if not compiler:
        for name in ['clang++','g++']:
            found=shutil.which(name)
            if found:compiler=[found];break
    if not compiler:
        spec=importlib.util.find_spec('ziglang')
        if spec:compiler=[str(Path(spec.origin).parent/('zig.exe' if platform.system()=='Windows' else 'zig')),'c++']
    if not compiler:raise SystemExit('No compiler found. Install clang/g++ or optional ziglang. Native results were not generated.')
    version=subprocess.check_output(compiler+['--version'],text=True).splitlines()[0]
    with tempfile.TemporaryDirectory(prefix='phase-ring-native-') as folder:
        executable=Path(folder)/('benchmark.exe' if platform.system()=='Windows' else 'benchmark')
        flags=['-O3','-std=c++17']
        build=subprocess.run(compiler+flags+[str(ROOT/'native/benchmark.cpp'),'-o',str(executable)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if build.returncode:
            raise RuntimeError('C++ compilation failed:\n'+build.stdout[-5000:])
        subprocess.run([str(executable),str(ROOT/'results')],check=True)
    info=dict(compiler=version,flags=flags,threads=1,platform=platform.platform(),processor=platform.processor(),logical_cpus=os.cpu_count(),
        measured_at_utc=datetime.fromtimestamp((ROOT/'results/native_samples.csv').stat().st_mtime,timezone.utc).isoformat(),
        lut_storage='Paired int16 Q15 values, 4/8 KiB; integer-to-float conversion and scaling inside timed loops',
        allocation='Preallocated output and operand arrays; allocation excluded for all native methods',
        input='C++ mt19937 seed 20261020, uniform angles in [-pi,pi); same native inputs for all methods; different dataset from NumPy run',
        limitations='Separate fused-loop study; not an isolated language-speed comparison and not PIM hardware evidence')
    (ROOT/'results/native_environment.json').write_text(json.dumps(info,indent=2),encoding='utf-8')

if __name__=='__main__':main()
