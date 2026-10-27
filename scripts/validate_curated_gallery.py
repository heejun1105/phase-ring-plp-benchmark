"""Check the topical article, shortened videos and unchanged original evidence."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from scripts.gallery_catalog import validate_gallery
from scripts.source_policy import validate_source
from scripts.render_curated_gallery import ROOT, FOLDER, ITEMS, renderer, source
from scripts.curated_video_edits import CUTS

BASE = 'bda78c67b4fd5f083da24f8d5ff375f50c0e0806'


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    count = 0
    def check(ok, label):
        nonlocal count
        if not ok:
            raise AssertionError(label)
        count += 1

    gallery = validate_gallery(ROOT, check)
    preserved = {}
    for row in subprocess.check_output(['git', 'ls-tree', '-r', BASE], cwd=ROOT, text=True, encoding='utf-8').splitlines():
        meta, name = row.split('\t', 1)
        path = ROOT/name
        freeze = name.startswith(('animations/', 'src/', 'native/', 'hardware/', 'tests/'))
        freeze |= name.startswith('results/') and path.suffix.lower() in ['.csv', '.npz', '.png']
        freeze |= name.startswith('scripts/') and path.name.startswith(('visualize_', 'baseline_', 'story_'))
        if freeze:
            data = path.read_bytes()
            blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            check(blob == meta.split()[2], 'Original evidence and full scene source retained: '+name)
            preserved[name] = hashlib.sha256(data).hexdigest()
    check(validate_source(ROOT)['source_id'] == 'VIII-EN', 'English paper is unchanged')

    # The article edits must retain actual plotted results before the loop fade.
    from scripts.baseline_precision_stairs import frame as stairs
    from scripts.baseline_wave_outputs import frame as waves
    for name, original, times in [
        ('curated_phase_precision', stairs, [.5, 3.0, 7.0]),
        ('curated_phase_outputs', waves, [.5, 4.8, 7.3]),
    ]:
        for t in times:
            check(np.array_equal(np.asarray(source(name, t)), np.asarray(original(t))), 'Unaltered numerical scene: '+name)
    from scripts.visualize_photo_noise import photo_noise
    from scripts.story_noise_lens import frame as lens
    for t in [.5, 2.8, 5.5]:
        check(np.array_equal(np.asarray(source('curated_photo_noise', t)), np.asarray(photo_noise(t))), 'Recorded full-photo scene retained')
    for t in [6.8, 8.8, 10.8]:
        check(np.array_equal(np.asarray(source('curated_photo_noise', t)), np.asarray(lens(t+4))), 'Recorded photo-detail scene retained')
    maps = [np.asarray(source('curated_noise_errors', t), dtype=np.int16) for t in [1.5, 5.5]]
    check(float(np.mean(np.abs(maps[0]-maps[1]))) > .5, 'Pixel and edge diagnostic maps differ')

    media = []
    for name in ITEMS:
        _, duration, _ = renderer(name)
        with Image.open(ROOT/f'animations/{name}.gif') as im:
            check(im.size == (960, 540) and im.info.get('loop') == 0, 'GIF dimensions and loop: '+name)
            targets = [int(t*1000)//40*40 for t in [0, duration*.25, duration*.5, duration*.75, duration-.92]]
            clock, errors, first, last = 0, [], None, None
            for i in range(im.n_frames):
                im.seek(i)
                ms = im.info.get('duration', 0)
                last = np.asarray(im.convert('RGB'), dtype=np.int16)
                if first is None:
                    first = last.copy()
                if any(clock <= t < clock+ms for t in targets):
                    expected = np.asarray(source(name, clock/1000).resize((960, 540), Image.Resampling.LANCZOS), dtype=np.int16)
                    error = float(np.mean(np.abs(last-expected)))
                    check(error < 9, 'Decoded GIF agrees with the shortened source: '+name)
                    errors.append(error)
                clock += ms
            minimum_frames = 2 if name == 'curated_noise_errors' else 30
            check(clock == int(duration*1000) and im.n_frames >= minimum_frames, 'GIF duration and frames: '+name)
            join = float(np.mean(np.abs(first-last)))
            check(join < 5, 'Continuous GIF loop: '+name)
            gif_frames = im.n_frames
        reader = imageio.get_reader(str(ROOT/f'animations/video/{name}.mp4'))
        meta, frames = reader.get_meta_data(), 0
        try:
            for frame in reader:
                check(frame.shape[:2] == (1080, 1920), 'Decoded MP4 dimensions: '+name)
                frames += 1
        finally:
            reader.close()
        check(frames == round(duration*24) and abs(meta['fps']-24) < .01 and abs(meta['duration']-duration) < .1, 'MP4 timing: '+name)
        media.append(dict(name=name, duration_seconds=duration, gif_frames=gif_frames, mp4_frames=frames,
            gif_max_source_mae=max(errors), loop_join_mae=join))

    readme = (ROOT/'README.md').read_text(encoding='utf-8')
    check(readme.count('https://doi.org/10.5281/zenodo.22782241') == 1, 'DOI appears once')
    check(readme.count('mailto:voodoo6000@daum.net') == 1, 'Author contact appears once')
    paragraphs = [p.strip() for p in readme.split('\n\n') if p.strip() and not p.startswith(('#', '|'))]
    check(len(paragraphs) == len(set(paragraphs)), 'No duplicate README paragraphs')
    for path in [ROOT/'README.md', *list((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith(('#', 'mailto:')):
                check((path.parent/target.split('#')[0]).exists(), 'Document link: '+target)
    old = subprocess.check_output(['git', 'show', BASE+':README.md'], cwd=ROOT, text=True, encoding='utf-8')
    record = dict(status='passed', check_count=count, baseline=BASE, gallery=gallery, media=media, cuts=CUTS,
        original_assets_and_scene_sources_preserved=len(preserved), new_benchmark_results=False,
        previous_embeds=len(re.findall(r'!\[[^\]]*\]\(animations/[^)]+\.gif\)', old)), current_embeds=gallery['selected_gifs'],
        previous_readme_words=len(old.split()), current_readme_words=len(readme.split()))
    (FOLDER/'validation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    (FOLDER/'preservation.json').write_text(json.dumps(dict(baseline=BASE, sha256=preserved), indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
