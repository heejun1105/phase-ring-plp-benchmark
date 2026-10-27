"""Check the one English source PDF explicitly supplied and approved by the owner."""
from pathlib import Path
import hashlib,json

ENGLISH_PATH='paper/Paper_VIII_Dual_Layer_Topological_Neuromorphic_Architecture.pdf'
ENGLISH_SHA256='d743c111e16aef248092c8bb077ae6edf79942103f6810c3bc4180e3e57faefc'
TRANSLATION_SHA256='249f651810bce6fab84693dd1049a3a551ab15e0b59893b5cd82a0461171ea41'

def validate_source(root):
    root=Path(root)
    manifest=json.loads((root/'results/source_manifest.json').read_text(encoding='utf-8'))
    assert manifest['source_id']=='VIII-EN' and manifest['sha256']==ENGLISH_SHA256,'Unexpected primary reference'
    assert manifest['repository_pdf_path']==ENGLISH_PATH and manifest['pdf_upload_authorized_by_user'] is True,'PDF inclusion must match the owner request'
    assert hashlib.sha256((root/ENGLISH_PATH).read_bytes()).hexdigest()==ENGLISH_SHA256,'English PDF bytes changed'
    assert manifest['page_count']==9 and manifest['paper_viii_pages']==[1,2,3,4,5] and manifest['appended_paper_ix_pages']==[6,7,8,9]
    assert manifest['previous_reference']['sha256']==TRANSLATION_SHA256,'Translation provenance missing'
    pdfs={p.relative_to(root).as_posix() for p in root.rglob('*.pdf') if '.git' not in p.parts and '.venv' not in p.parts}
    assert pdfs=={ENGLISH_PATH},'Only the owner-approved English paper may be included'
    return manifest
