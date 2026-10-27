"""Same-input conventional FP32 and phase-ring reference outputs for visual comparisons."""
from pathlib import Path
from functools import lru_cache
import csv
import numpy as np
from src import phase_ring as ring

ROOT=Path(__file__).resolve().parents[1]
WINDOW_DEG=6*360/1024
METRIC_METHODS=('FP32 summed-angle trig','Z1024 Q15 end-to-end','Z2048 Q15 end-to-end')
METHOD_KEYS=('fp32','z1024','z2048')
LABELS=('Conventional FP32','Z1024','Z2048')

def _phase(z):
    z=np.asarray(z)
    return np.rad2deg(np.arctan2(z.imag.astype(np.float64),z.real.astype(np.float64)))

@lru_cache(maxsize=2)
def _lut(n):return ring.make_lut(n)

def _decode(angle_deg,n):
    a=np.atleast_1d(np.deg2rad(np.asarray(angle_deg,dtype=np.float64)))
    return ring.decode(ring.quantize(a,n),_lut(n)).reshape(np.shape(angle_deg))

def _fields(ideal,fp32,z1024,z2048):
    values=dict(ideal=ideal,fp32=fp32,z1024=z1024,z2048=z2048)
    for key in list(values):values[key+'_deg']=_phase(values[key])
    return values

def sample(angle_deg):
    """Reconstruct one angle; all outputs are complex64 except the ideal reference."""
    theta=np.deg2rad(np.asarray(angle_deg,dtype=np.float64))
    ideal=np.cos(theta)+1j*np.sin(theta)
    return _fields(ideal,ideal.astype(np.complex64),_decode(angle_deg,1024),_decode(angle_deg,2048))

def product(a_deg,b_deg):
    """Quantize each ring input separately; use the optimized summed-angle FP32 route."""
    a,b=np.broadcast_arrays(np.asarray(a_deg,dtype=np.float64),np.asarray(b_deg,dtype=np.float64))
    theta=np.deg2rad(a)+np.deg2rad(b)
    ideal=np.cos(theta)+1j*np.sin(theta);outputs=[]
    for n in [1024,2048]:
        aa=ring.quantize(np.atleast_1d(np.deg2rad(a)),n)
        bb=ring.quantize(np.atleast_1d(np.deg2rad(b)),n)
        outputs.append(ring.decode(ring.add(aa,bb,n),_lut(n)).reshape(a.shape))
    return _fields(ideal,ideal.astype(np.complex64),*outputs)

def input_angle(t):return WINDOW_DEG*(.5-.44*np.cos(np.asarray(t)*np.pi*2/8))

@lru_cache(maxsize=1)
def native_metrics():
    with (ROOT/'results/native_audit_benchmark.csv').open() as f:
        timings={r['method']:r for r in csv.DictReader(f) if int(r['n'])==10000000}
    with (ROOT/'results/native_audit_accuracy.csv').open() as f:
        accuracy={r['method']:r for r in csv.DictReader(f) if int(r['n'])==10000000}
    return {m:{**timings[m],**accuracy[m]} for m in METRIC_METHODS}
