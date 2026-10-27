# Additional visual explanations

The earlier videos remain intact and visible in the README. These five new
GIF/MP4 pairs add other ways to understand the same material. No previous
animation or measurement is replaced.

| New file name | Length | Visible idea |
| --- | ---: | --- |
| phase_wave_basics | 14 s | The hand on a circle and a point on a sine wave move together |
| calculate_or_lookup | 16 s | Calculate a wave answer again, or read a prepared answer from a table |
| angle_snap_targets | 16 s | A smooth white target and real quantized followers on a shared angle track |
| wrap_and_fetch | 18 s | A token passes the last stored position, wraps and selects an answer |
| noise_detail_lens | 18 s | The same sky and tripod patches enlarged from noisy and filtered photos |

Each has a 1920x1080, 24 fps H.264 MP4 and a 960x540 looping GIF at nominal
25 fps for the four angle/ring stories and 20 fps for the photo lens to keep its
download size manageable. Repeated frames may be merged while preserving duration. The last
0.8 seconds blends back to the opening frame. A shared palette reserves the
theme colors, including amber for visible gaps and discarded laps.

## What stays tied to the source data

The basic circle and wave use the same sine value at their marked point. The
second scene changes starting phase without changing wave height. This is a
mathematical illustration, with no measured runtime or device claim.

The calculate/lookup example uses the existing quarter-bin input angles, which
quantize to 750 and 400 in Z1024. They wrap to address 126, read paired Q15
values (23452,22883), and produce a wave differing by approximately 0.1762
degrees from the conventional complex64 result. Scene pacing is equal for
explanation; the separate CPU race supplies the measured performance comparison.

The target tracks use one magnified 0-2.109375-degree window and one common
horizontal pixel/degree scale. Only the orange horizontal span represents
angle error; vertical separation distinguishes symbols. Followers use the
actual floor quantizer, not an invented visual error. The separate 0.29° + 0.29°
example quantizes each input before adding. Final RMSE values are the retained
200,000-pair accuracy checks in the 10M native audit, not statistics measured
from the moving target. More stored positions do not establish a speed ranking.

The wrap examples replay integer increments from 1023+1, 750+400 and 1500+800.
Their final indices are 0,126,252 and their scalar sine Q15 words are
0,22883,22883. The first six-position strip is explicitly a magnified local
view. A completed lap can fold away, but the displayed final address always
comes from the actual modular sum. This is not a memory-chip timing trace.

The photo lens crops the same committed camera arrays at the same coordinates,
zoom and grayscale mapping. Bilateral, V1 and V2 outputs are complete before
the lens moves. Metrics refer to the full unscaled camera case at noise sigma 0.06,
seed 20261020. The lens and transitions are comparison effects, not progressive
denoising or clean-reference input to a filter. These are PLP-Inspired
Experimental Prototypes, not validated implementations of the original PLP
equations. The CPU phase timings do not describe these image-filter runtimes.

## Reproduce and review

```bash
python -m scripts.render_story_variants --preview-only
python -m scripts.render_story_variants
python -m scripts.public_gallery
python -m scripts.validate_story_variants
```

Use `--only <file_name>` to render one version. Existing media uses different
filenames and remains unchanged. The new source modules are listed by the
registry in [render_story_variants.py](../scripts/render_story_variants.py).
Full-size and 720-pixel review frames are saved in
[results/story_variants](../results/story_variants).

The gallery check requires every GIF under `animations/` to be embedded directly
in the README, outside collapsed sections, with an MP4 link. It also checks
previous media hashes, mathematical examples, recorded image/accuracy data,
decoded GIF/source agreement, looping joins, MP4 frames, English text and links.
No human comprehension study or new performance experiment is claimed.

The owner's Paper VIII DOI and email are placed at the end of the README.
[Paper VIII - Zenodo](https://doi.org/10.5281/zenodo.22782241) ·
[Author email](mailto:voodoo6000@daum.net)
