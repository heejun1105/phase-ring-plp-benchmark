"""Non-destructive editorial cuts of existing, recorded-data visualizations.

These four renderers only select source scenes and apply documented editorial
holds or dissolves. They do not change a filter, reference calculation, image
crop, error scale, measured value, or original media file. The shared exporter
applies the final loop dissolve to each new clip.
"""
from functools import lru_cache

from PIL import Image

from scripts.visual_style import ease

CUTS = {
    'curated_phase_precision': {
        'function': 'precision', 'duration': 10.0, 'poster': 3.0,
        'title': 'A smooth conventional result and two stored-angle grids',
        'description': 'Three equal panels show actual reconstructed phases on the same magnified angle scale. Repeated native result cards are omitted.',
        'segments': [
            {'start': 0.0, 'end': 10.0, 'source': 'scripts.baseline_precision_stairs.frame',
             'source_start': 0.0, 'source_end': 10.0, 'kind': 'unchanged scene cut'},
        ],
        'omitted': [{'source_start': 10.5, 'source_end': 15.0, 'reason': 'Repeated native time and RMSE endcard'}],
        'preview_times': [0.6, 2.5, 4.8, 6.8, 8.2, 9.0],
    },
    'curated_phase_outputs': {
        'function': 'phase_outputs', 'duration': 9.0, 'poster': 7.3,
        'title': 'The same three computed waves, enlarged together',
        'description': 'The original full-scale wave view moves into one common zero-crossing close-up. Repeated native result cards are omitted.',
        'segments': [
            {'start': 0.0, 'end': 9.0, 'source': 'scripts.baseline_wave_outputs.frame',
             'source_start': 0.0, 'source_end': 9.0, 'kind': 'unchanged scene cut'},
        ],
        'omitted': [{'source_start': 9.4, 'source_end': 14.0, 'reason': 'Repeated native time and RMSE endcard'}],
        'preview_times': [0.6, 2.8, 4.8, 6.4, 7.5, 8.0],
    },
    'curated_photo_noise': {
        'function': 'photo_noise', 'duration': 12.0, 'poster': 5.5,
        'title': 'One real photograph, then its sky and tripod pixels',
        'description': 'Full-photo wipes show Bilateral, V1 and V2. A labeled V2 detail lens then visits sky noise and a tripod edge, without repeating synthetic fixtures or scorecards.',
        'segments': [
            {'start': 0.0, 'end': 6.0, 'source': 'scripts.visualize_photo_noise.photo_noise',
             'source_start': 0.0, 'source_end': 6.0, 'kind': 'unchanged full-photo scenes'},
            {'start': 6.0, 'end': 11.0, 'source': 'scripts.story_noise_lens.frame',
             'source_start': 10.0, 'source_end': 15.0, 'source_end_exclusive': True,
             'kind': 'unchanged V2 sky-to-tripod detail scene'},
            {'start': 11.0, 'end': 12.0, 'source': 'scripts.story_noise_lens.frame',
             'source_start': 14.999, 'source_end': 14.999, 'kind': 'editorial final-detail hold'},
        ],
        'omitted': [
            {'source': 'scripts.visualize_photo_noise.photo_noise', 'source_start': 6.0,
             'source_end': 18.0, 'reason': 'Synthetic-detail tour and repeated camera/suite scorecards'},
            {'source': 'scripts.story_noise_lens.frame', 'source_start': 15.0,
             'source_end': 18.0, 'reason': 'Repeated three-result comparison'},
        ],
        'preview_times': [0.6, 2.8, 5.5, 6.8, 8.8, 10.8],
    },
    'curated_noise_errors': {
        'function': 'noise_errors', 'duration': 8.0, 'poster': 1.5,
        'title': 'Pixel and edge errors on shared diagnostic scales',
        'description': 'Only the existing absolute-pixel and Sobel-magnitude error maps are shown. Removed-intensity maps and the clean reference remain; repeated image tours and suite scorecards are omitted.',
        'segments': [
            {'start': 0.0, 'end': 3.6, 'source': 'scripts.visualize_noise_v4._heatmap',
             'source_start': 9.8, 'source_end': 9.8, 'kind': 'editorial pixel-map inspection hold'},
            {'start': 3.6, 'end': 4.0, 'source': 'scripts.visualize_noise_v4._heatmap',
             'source_start': 9.8, 'source_end': 11.2,
             'kind': 'editorial dissolve between completed diagnostic views'},
            {'start': 4.0, 'end': 8.0, 'source': 'scripts.visualize_noise_v4._heatmap',
             'source_start': 11.2, 'source_end': 11.2, 'kind': 'editorial edge-map inspection hold'},
        ],
        'omitted': [
            {'source_start': 0.0, 'source_end': 9.2, 'reason': 'Image comparisons already covered by adjacent clips'},
            {'source_start': 12.0, 'source_end': 15.0, 'reason': 'Repeated V1/V2 suite scorecard'},
        ],
        'preview_times': [0.6, 2.8, 3.8, 4.7, 6.0, 6.9],
    },
}

for _item in CUTS.values():
    _item['loop_dissolve_seconds'] = 0.8


def precision(t, study=None):
    from scripts.baseline_precision_stairs import frame
    return frame(min(9.999999, max(0.0, float(t))), study)


def phase_outputs(t, study=None):
    from scripts.baseline_wave_outputs import frame
    return frame(min(8.999999, max(0.0, float(t))), study)


def photo_noise(t, study=None):
    t = max(0.0, float(t))
    if t < 6.0:
        from scripts.visualize_photo_noise import photo_noise as original
        return original(t, study)
    from scripts.story_noise_lens import frame
    return frame(min(14.999, 10.0 + t - 6.0), study)


@lru_cache(maxsize=1)
def _diagnostic_frames():
    from scripts.visualize_v3 import Study
    from scripts.visualize_noise_v4 import _heatmap
    study = Study()
    return _heatmap(9.8, study), _heatmap(11.2, study)


def noise_errors(t, study=None):
    pixel, edge = _diagnostic_frames()
    if t < 3.6:
        return pixel.copy()
    if t < 4.0:
        return Image.blend(pixel, edge, ease((float(t) - 3.6) / 0.4))
    return edge.copy()
