"""The curated reading order and linked archive share one explicit media catalog.

Selection changes presentation only. Unselected GIF/MP4 pairs remain on disk,
under their existing names, and must be indexed by topic in the media archive.
"""
from pathlib import Path
import re

ARCHIVE_PATH = 'docs/media_archive.md'
SECTIONS = (
    dict(id='wave-angle-calculation', heading='Wave-angle calculation', media=(
        'public_cpu_workflow', 'phase_wave_basics', 'calculate_or_lookup',
        'wrap_and_fetch', 'curated_phase_precision', 'curated_phase_outputs')),
    dict(id='photograph-denoising', heading='Photograph denoising', media=(
        'curated_photo_noise', 'curated_noise_errors', 'edge_preservation_comparison')),
)
SELECTED = tuple(name for section in SECTIONS for name in section['media'])

# Every retained video has an explicit topic. A newly added video needs an
# intentional catalog entry rather than silently falling into a default topic.
TOPIC_MEDIA = {
    'wave-angle-calculation': (
        'public_cpu_workflow', 'native_cpp_performance', 'benchmark_speed_race',
        'phase_wave_basics', 'calculate_or_lookup', 'public_phase_computing',
        'computing_architecture', 'computing_comparison', 'wrap_and_fetch',
        'phase_bits_to_lut', 'phase_overflow_lut', 'curated_phase_precision',
        'public_phase_precision', 'angle_snap_targets', 'phase_precision_comparison',
        'curated_phase_outputs', 'fp32_and_phase_outputs',
        'project_overview', 'legacy_two_settings_angle_targets',
        'legacy_two_settings_phase_precision', 'legacy_two_settings_public_precision'),
    'photograph-denoising': (
        'curated_photo_noise', 'photo_noise_comparison', 'noise_detail_lens',
        'curated_noise_errors', 'noise_reduction_comparison',
        'edge_preservation_comparison', 'noise_comparison'),
}


def all_media(root):
    """Return all retained top-level GIF stems, sorted for stable records."""
    return tuple(sorted(p.stem for p in (Path(root)/'animations').glob('*.gif')))


def validate_catalog(root):
    """Check the complete catalog and pairs; return excluded GIF stems."""
    root = Path(root)
    actual = all_media(root)
    declared = tuple(name for names in TOPIC_MEDIA.values() for name in names)
    assert len(SELECTED) == len(set(SELECTED)), 'A selected video appears more than once'
    assert len(declared) == len(set(declared)), 'A video has more than one archive topic'
    assert set(actual) == set(declared), 'The catalog must cover every retained GIF exactly once'
    assert set(SELECTED) <= set(actual), 'Every selected video must exist'
    for section in SECTIONS:
        assert set(section['media']) <= set(TOPIC_MEDIA[section['id']]), 'Selected video has the wrong topic'
    for name in actual:
        assert (root/f'animations/video/{name}.mp4').is_file(), 'Missing paired MP4: '+name
    return tuple(name for name in actual if name not in SELECTED)


def archive_sections(root):
    """Return the same topic sections containing only unselected video stems."""
    excluded = set(validate_catalog(root))
    return tuple(dict(id=section['id'], heading=section['heading'],
        media=tuple(name for name in TOPIC_MEDIA[section['id']] if name in excluded))
        for section in SECTIONS)


def _local_media(target, document, root, suffix):
    target = target.strip().strip('<>').split('#', 1)[0].split('?', 1)[0]
    if '://' in target or target.startswith(('mailto:', '#')):
        return None
    path = (document.parent/target).resolve()
    folder = root/'animations' if suffix == '.gif' else root/'animations/video'
    return path.stem if path.suffix.lower() == suffix and path.parent == folder.resolve() else None


def _document_media(document, root):
    """Track main headings and collapse state without losing duplicate embeds."""
    text = document.read_text(encoding='utf-8')
    heading, depth = None, 0
    headings, images, links = [], [], []
    for line_no, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^##\s+(.+?)\s*$', line)
        if match:
            heading = match.group(1)
            headings.append((heading, line_no))
        # Events are processed in textual order, including one-line details.
        pattern = r'<details\b[^>]*>|</details\s*>|!\[[^\]]*\]\(([^)]+)\)|<img\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>'
        for event in re.finditer(pattern, line, re.I):
            token = event.group(0)
            if token.lower().startswith('<details'):
                depth += 1
            elif token.lower().startswith('</details'):
                depth -= 1
                assert depth >= 0, f'Unmatched details tag in {document.name}:{line_no}'
            else:
                name = _local_media(event.group(1) or event.group(2), document, root, '.gif')
                if name:
                    images.append(dict(name=name, heading=heading, depth=depth, line=line_no))
        for match in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', line):
            for suffix in ['.gif', '.mp4']:
                name = _local_media(match.group(1), document, root, suffix)
                if name:
                    links.append(dict(name=name, suffix=suffix, heading=heading, line=line_no))
    assert depth == 0, 'Unclosed details tag in '+document.name
    return dict(text=text, headings=headings, images=images, links=links)


def validate_gallery(root, check=None):
    """Validate unique topical embeds and the complete link-only media archive.

    Pass a validator's check(bool, label) to include these checks in its counter.
    Numerical, source-preservation and decoded-media checks remain in their
    existing validators and are not replaced by this presentation check.
    """
    root = Path(root).resolve()
    if check is None:
        def check(ok, label):
            if not ok:
                raise AssertionError(label)
    excluded = validate_catalog(root)
    check(True, 'Catalog covers all retained GIF/MP4 pairs with unique topics')
    readme_path = root/'README.md'
    readme = _document_media(readme_path, root)
    images = readme['images']
    check(tuple(row['name'] for row in images) == SELECTED,
        'README embeds exactly the selected videos once, in the curated order')
    check(all(row['depth'] == 0 for row in images), 'Selected videos are visible outside collapsed details')
    heading_names = [name for name, _ in readme['headings']]
    positions = []
    for section in SECTIONS:
        heading = section['heading']
        check(heading_names.count(heading) == 1, 'One main topic heading: '+heading)
        positions.append(heading_names.index(heading))
        for name in section['media']:
            check(any(row['name'] == name and row['heading'] == heading for row in images),
                'Selected video stays inside its topic group: '+name)
            check(any(row['name'] == name and row['suffix'] == '.mp4' and row['heading'] == heading for row in readme['links']),
                'Selected video keeps an MP4 link in its topic group: '+name)
    check(positions == list(range(positions[0], positions[0]+len(SECTIONS))),
        'The main topic groups are adjacent and ordered')
    archive_links = re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', readme['text'])
    check(any(target.strip().split('#', 1)[0] in [ARCHIVE_PATH, './'+ARCHIVE_PATH] for target in archive_links),
        'README links the separate media archive')
    archive_path = root/ARCHIVE_PATH
    check(archive_path.is_file(), 'The media archive exists')
    archive = _document_media(archive_path, root)
    check(not archive['images'] and not re.search(r'!\[[^\]]*\]\(|<(?:img|video)\b', archive['text'], re.I),
        'The archive links videos without embedding or autoplaying them')
    for section in archive_sections(root):
        heading = section['heading']
        check([name for name, _ in archive['headings']].count(heading) == 1,
            'One matching archive topic heading: '+heading)
        for name in section['media']:
            for suffix in ['.gif', '.mp4']:
                rows = [row for row in archive['links'] if row['name'] == name and row['suffix'] == suffix]
                check(len(rows) == 1 and rows[0]['heading'] == heading,
                    'Excluded video is linked once under its archive topic: '+name+suffix)
    archived_names = {row['name'] for row in archive['links']}
    check(set(excluded) <= archived_names, 'Every excluded video remains indexed in the archive')
    return dict(selected_gifs=len(SELECTED), archived_gifs=len(excluded), retained_gif_mp4_pairs=len(all_media(root)),
        topic_groups=[dict(id=s['id'], heading=s['heading'], media=list(s['media'])) for s in SECTIONS],
        selected_order=list(SELECTED), archive=ARCHIVE_PATH, archive_embeds=False,
        organization='Unique selected embeds in contiguous topic groups; excluded pairs indexed by the same topics')


if __name__ == '__main__':
    import json
    print(json.dumps(validate_gallery(Path(__file__).resolve().parents[1]), indent=2))
