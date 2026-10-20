"""Standard scientific plots and exact shared-scale heatmaps for the expanded study."""
from pathlib import Path
import collections,csv,json,statistics
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
COLORS={'Clean':'#ffffff','Legacy V1':'#60a5fa','Prototype V2':'#35e0bf','Bilateral':'#f0c36b'}

def read(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def main():
    folder=ROOT/'results/visual_study';rows=read('expanded_noise.csv');ab=read('noise_ablation.csv');out=[]
    grouped=collections.defaultdict(list)
    for r in rows:grouped[r['method']].append(r)
    for method,rs in grouped.items():
        x=dict(method=method,cases=len(rs))
        for key in ['psnr_db','ssim','edge_preservation','median_ms']:
            values=[float(r[key]) for r in rs];x[key]=statistics.mean(values);x['sd_'+key]=statistics.stdev(values)
        out.append(x)
    from src.benchmark.run import write_csv
    write_csv(ROOT/'results/expanded_summary.csv',out)
    # Color mapping is identical for every method and scene; no per-image normalization.
    for name in ['microtext','geometry','camera','dark_texture']:
        bundle=np.load(folder/f'{name}_outputs.npz');clean=bundle['clean']
        def grad(x):return np.hypot(cv2.Sobel(x,cv2.CV_32F,1,0),cv2.Sobel(x,cv2.CV_32F,0,1))
        gc=grad(clean)
        for key in ['clean','noisy','bilateral','legacy_v1','prototype_v2']:
            x=bundle[key]
            for mode,error,scale in [('error',np.abs(x-clean),0.20),('edge',np.abs(grad(x)-gc),1.0),('removed',np.abs(bundle['noisy']-x),0.20)]:
                rgb=(matplotlib.colormaps['magma'](np.clip(error/scale,0,1))[...,:3]*255).astype(np.uint8)
                Image.fromarray(rgb).save(folder/f'{name}_{key}_{mode}.png')
        # Profiles use true values, not sharpened or contrast-stretched outputs.
        y=120 if name=='microtext' else (140 if name=='geometry' else 256)
        fig,ax=plt.subplots(figsize=(11.5,3.0),dpi=100,facecolor='#0d1728');ax.set_facecolor('#0d1728')
        for key,label in [('clean','Clean'),('legacy_v1','Legacy V1'),('prototype_v2','Prototype V2')]:
            ax.plot(np.arange(512),bundle[key][y],label=label,color=COLORS[label],lw=1.6)
        ax.set(xlim=(15,495),ylim=(0,0.25 if name=='dark_texture' else 1),xlabel='Pixel x',ylabel='Intensity [0,1]')
        ax.set_xticks([100,200,300,400]);ax.set_yticks([0,0.1,0.2] if name=='dark_texture' else [0,0.5,1])
        ax.tick_params(colors='#a8bad2',labelsize=19);ax.xaxis.label.set_color('#a8bad2');ax.yaxis.label.set_color('#a8bad2')
        ax.xaxis.label.set_fontsize(19);ax.yaxis.label.set_fontsize(19)
        for spine in ax.spines.values():spine.set_color('#30415b')
        ax.grid(alpha=0.12);leg=ax.legend(loc='upper right',ncol=3,fontsize=18,facecolor='#0d1728',edgecolor='#30415b')
        for text in leg.get_texts():text.set_color('#e7efff')
        fig.tight_layout();fig.savefig(folder/f'{name}_profile.png');plt.close(fig)
    # A compact suite-wide plot prevents a single favorable image from defining the story.
    labels=['Bilateral','Legacy V1','Prototype V2'];means={r['method']:r for r in out}
    fig,axes=plt.subplots(1,3,figsize=(15,4),dpi=140,facecolor='#09111e')
    for ax,key,title in zip(axes,['psnr_db','edge_preservation','median_ms'],['Mean PSNR (dB)','Mean edge fidelity','Mean of per-case timing medians (ms)']):
        ax.set_facecolor('#101d30');v=[means[x][key] for x in labels]
        ax.bar(labels,v,color=[COLORS[x] for x in labels]);ax.set_title(title,color='white',fontsize=12)
        for j,value in enumerate(v):ax.text(j,value*1.025,f'{value:.3f}',ha='center',color='white',fontsize=11)
        ax.set_ylim(0,max(v)*1.18);ax.tick_params(colors='#a8bad2');ax.spines[['top','right']].set_visible(False)
    fig.suptitle('All 54 cases; fixed settings, no best-case selection',color='white',fontsize=16)
    fig.tight_layout();fig.savefig(folder/'suite_tradeoffs.png');plt.close(fig)
    summary={r['method']:r for r in out}
    (folder/'study_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('Generated shared-scale error/edge maps, profiles and suite summaries.',flush=True)

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT));main()
