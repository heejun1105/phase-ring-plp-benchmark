"""Small numerical checks of displayed source-paper claims, not a general proof review."""
from pathlib import Path
import json,math
import numpy as np

def main():
    q=63/64;n=1024;p1,p2=3,5;k=np.arange(1,n+1)
    cross=np.mean(np.exp(2j*np.pi*k/p1)*np.exp(-2j*np.pi*k/p2))
    values={'contraction_factor':q,'six_step_bound_relative_to_initial':q**6,
            'steps_for_bound_below_0_001':math.ceil(math.log(0.001)/math.log(q)),
            'prime_sum_counterexample':{'N':n,'p1':p1,'p2':p2,'magnitude':float(abs(cross)),
                'real':float(cross.real),'imag':float(cross.imag),'expected_by_exact_delta_claim':0},
            'pixels_per_second_for_4k_in_0_08ms':3840*2160/0.00008}
    root=Path(__file__).resolve().parents[1]
    (root/'results/claim_audit.json').write_text(json.dumps(values,indent=2),encoding='utf-8')
    print(json.dumps(values,indent=2))

if __name__=='__main__':main()
