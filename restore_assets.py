"""Idempotently unpack trusted site assets when checking out the GitHub repository.

All archive paths are validated; never write outside static/assets.
"""
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'static' / 'assets'
ARCHIVE = ROOT / 'assets-bundle.zip'
if ARCHIVE.is_file() and not (ASSETS / 'covers' / 'e01.webp').is_file():
    with ZipFile(ARCHIVE) as z:
        for entry in z.infolist():
            name = entry.filename.replace('\\', '/')
            if entry.is_dir(): continue
            if not name.startswith('static/assets/') or '..' in Path(name).parts:
                raise ValueError('Unsafe asset archive path')
            destination = (ROOT / name).resolve()
            if not destination.is_relative_to(ASSETS.resolve()):
                raise ValueError('Asset escaped output directory')
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(z.read(entry))
    print('Restored museum cover and monkey assets.')