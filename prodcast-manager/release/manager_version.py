"""Stamp the release version and verify the value embedded by PyInstaller."""
import argparse
from pathlib import Path
import re


def normalize(value):
    if not re.fullmatch(r'v?[0-9]+\.[0-9]+\.[0-9]+',value):
        raise ValueError('Expected stable Manager release version vMAJOR.MINOR.PATCH')
    return value.removeprefix('v')


def stamp(path,version):
    version=normalize(version)
    source=path.read_text(encoding='utf-8')
    source,count=re.subn(r"(?m)^__version__\s*=\s*['\"][^'\"]+['\"]\s*$",f"__version__ = '{version}'",source)
    if count!=1:raise ValueError('Expected exactly one Manager version declaration')
    path.write_text(source+'\n',encoding='utf-8')


def verify(exe,version):
    from PyInstaller.archive.readers import CArchiveReader
    expected=normalize(version)
    archive=CArchiveReader(str(exe)).open_embedded_archive('PYZ.pyz')
    code=archive.extract('prodcast_manager')
    versions=[v for v in code.co_consts if isinstance(v,str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',v)]
    if '__version__' not in code.co_names or versions!=[expected]:
        raise ValueError(f'Manager EXE internal version mismatch: expected {expected}, found {versions}')
    print(f'Verified Manager EXE internal version: {expected}')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('version');parser.add_argument('--verify-exe',type=Path)
    args=parser.parse_args()
    if args.verify_exe:verify(args.verify_exe,args.version)
    else:stamp(Path(__file__).resolve().parents[1]/'prodcast_manager/__init__.py',args.version)
