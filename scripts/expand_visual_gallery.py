"""Keep every animation visible in the README and add the alternative explanations."""
from scripts.render_story_variants import ITEMS

EARLIER=[
 ('native_cpp_performance','Native timing and accuracy','The earlier native CPU race includes both formula baselines and the measured approximation errors.'),
 ('computing_architecture','Detailed computational architecture','The shared inputs travel through complex arithmetic or quantization, addition and a paired lookup.'),
 ('benchmark_speed_race','NumPy CPU race','The separate NumPy experiment shows kernel and full-pipeline timings. Kernel output types differ; see its scope labels.'),
 ('phase_overflow_lut','Overflow and addressed memory','A phase dial, register carry and selected lookup word remain linked through the rollover examples.'),
 ('phase_precision_comparison','Precision as actual stair steps','This earlier view uses an angle plot to show floor quantization in a magnified four-degree window.'),
 ('noise_reduction_comparison','Text, edges and image errors','The recorded text/edge comparison adds common-scale error maps after actual image views.'),
 ('edge_preservation_comparison','Noise quality and edge tradeoffs','Actual V1/V2 profiles expose detail attenuation, residual noise and processing-time differences.'),
 ('computing_comparison','First arithmetic demonstration','The first edition combines rollover examples with measured CPU scopes. It remains available for comparison.'),
 ('noise_comparison','First image-stage demonstration','The first edition tours the recorded local shrinkage, guided smoothing and final quantization stages.')]

def card(name,title,caption):
    return f'### {title}\n\n![{title}](animations/{name}.gif)\n\n{caption}\n\n[MP4](animations/video/{name}.mp4) · [GIF](animations/{name}.gif)\n\n'

def expand(text):
    new='## More ways to understand the same idea\n\nThese are additional versions. Start with the circle and wave, then follow the stored-answer shortcut, angle error, wrapping and photo details. The earlier videos remain visible farther down this page.\n\n'
    for name,(_,title,caption) in ITEMS.items():new+=card(name,title,caption)
    new+='[New renderers and reproduction](docs/story_variants.md) · [All preserved measurements](docs/measurements.md)\n\n'
    text=text.replace('## The three explanation videos',new+'## The earlier explanation versions')
    text=text.replace('These explain the calculation shortcut above. They are not three more performance results, and you can skip the bit-level check when viewing the main results.',
        'These versions show the same topics with more numerical or technical detail. They remain embedded here alongside the simpler versions.')
    for marker,name,title in [
        ('**How the calculation changes.**','public_phase_computing','Earlier calculation routes'),
        ('**What precision the shortcut loses.**','public_phase_precision','Earlier precision terraces'),
        ('**Whether the bits select the right answer.**','phase_bits_to_lut','Detailed bit and LUT replay')]:
        text=text.replace(marker,f'![{title}](animations/{name}.gif)\n\n'+marker)
    marker='[A short guide to these demos]'
    text=text.replace(marker,'![The existing project overview](animations/project_overview.gif)\n\n'+marker)
    marker='<details>\n<summary>Earlier videos and review records</summary>'
    if marker not in text:raise ValueError('Expected earlier-video section was not found')
    head,_=text.split(marker,1)
    old='## More existing versions\n\nAll earlier GIFs remain embedded below. No video has been removed or replaced.\n\n'
    for name,title,caption in EARLIER:old+=card(name,title,caption)
    old+='[Previous visual review](docs/visual_quality.md) · [Noise revision](docs/noise_visual_revision.md) · [Previous validation](results/validation.json) · [Source manifest before the English upload](results/archive/source_manifest_viii_ko.json)\n'
    contact='\n## Paper and author\n\nPaper VIII — Zenodo: [10.5281/zenodo.22782241](https://doi.org/10.5281/zenodo.22782241)\n\nAuthor email: [voodoo6000@daum.net](mailto:voodoo6000@daum.net)\n'
    return head+old+contact
