"""Keep the original two-setting videos when their current versions gain FP32 baselines."""
from pathlib import Path
import hashlib,shutil

ROOT=Path(__file__).resolve().parents[1]
ARCHIVES={
 'phase_precision_comparison':'legacy_two_settings_phase_precision',
 'public_phase_precision':'legacy_two_settings_public_precision',
 'angle_snap_targets':'legacy_two_settings_angle_targets',
}
ORIGINAL_SHA256={
 'phase_precision_comparison.gif':'faa60261a69703accd8ac6bcab43b9069cdb6c734ce7e9b683cf5ea137e0d829',
 'phase_precision_comparison.mp4':'e22c26c5e17d3f6ca15fde7c2ebd45f0bcec5c828eef0c0fb41a9947cb4a996a',
 'public_phase_precision.gif':'88c6d605a2f79877bfcd01d3514aceda8792ae3edb9545b4eeea25ce1cc4dbe4',
 'public_phase_precision.mp4':'0b7f4ba0520b1b9189fe87ff2b71f64ecc2da9550acfb1ea5c76bbc6414b01ff',
 'angle_snap_targets.gif':'032ec7390c08d79764fdb4e986dfbe48b3791bbd3eabb25ab542d585c45cea91',
 'angle_snap_targets.mp4':'c5761720abb961f836d45932b82762558a393d65452c57918292d41363dd0c42',
}

def historical_path(relative):
    p=Path(relative)
    if p.stem in ARCHIVES and p.suffix in ['.gif','.mp4'] and p.parts[0]=='animations':
        archived=p.with_name(ARCHIVES[p.stem]+p.suffix)
        if (ROOT/archived).exists():return archived.as_posix()
    return p.as_posix()

def archive_originals():
    manifest={}
    for old,new in ARCHIVES.items():
        for folder,extension in [('animations','.gif'),('animations/video','.mp4')]:
            original=ROOT/folder/(old+extension);archive=ROOT/folder/(new+extension)
            candidate=archive if archive.exists() else original
            if hashlib.sha256(candidate.read_bytes()).hexdigest()!=ORIGINAL_SHA256[old+extension]:
                raise AssertionError('Original media must be restored from the previous revision: '+str(candidate))
            if not archive.exists():shutil.copyfile(original,archive)
            manifest[original.relative_to(ROOT).as_posix()]=dict(archived_as=archive.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    return manifest
