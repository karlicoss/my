"""
Various helpers for compression
"""
from __future__ import annotations

import pathlib
from pathlib import Path
from typing import Union, IO
import io

PathIsh = Union[Path, str]


class Ext:
    xz    = '.xz'
    zip   = '.zip'
    lz4   = '.lz4'
    zstd  = '.zstd'
    targz = '.tar.gz'


def is_compressed(p: Path) -> bool:
    # todo kinda lame way for now.. use mime ideally?
    # should cooperate with kompress.kopen?
    return any(p.name.endswith(ext) for ext in {Ext.xz, Ext.zip, Ext.lz4, Ext.zstd, Ext.targz})


def _zstd_open(path: Path, *args, **kwargs) -> IO[str]:
    import zstandard as zstd # type: ignore
    fh = path.open('rb')
    dctx = zstd.ZstdDecompressor()
    reader = dctx.stream_reader(fh)
    return io.TextIOWrapper(reader, **kwargs) # meh


# TODO returns protocol that we can call 'read' against?
# TODO use the 'dependent type' trick?
def kopen(path: PathIsh, *args, mode: str='rt', **kwargs) -> IO[str]:
    # TODO handle mode in *rags?
    encoding = kwargs.get('encoding', 'utf8')
    kwargs['encoding'] = encoding

    pp = Path(path)
    name = pp.name
    if name.endswith(Ext.xz):
        import lzma
        r = lzma.open(pp, mode, *args, **kwargs)
        # should only happen for binary mode?
        # file:///usr/share/doc/python3/html/library/lzma.html?highlight=lzma#lzma.open
        assert not isinstance(r, lzma.LZMAFile), r
        return r
    elif name.endswith(Ext.zip):
        # eh. this behaviour is a bit dodgy...
        from zipfile import ZipFile
        zfile = ZipFile(pp)

        [subpath] = args # meh?

        ## oh god... https://stackoverflow.com/a/5639960/706389
        ifile = zfile.open(subpath, mode='r')
        ifile.readable = lambda: True  # type: ignore
        ifile.writable = lambda: False # type: ignore
        ifile.seekable = lambda: False # type: ignore
        ifile.read1    = ifile.read    # type: ignore
        # TODO pass all kwargs here??
        # todo 'expected "BinaryIO"'??
        return io.TextIOWrapper(ifile, encoding=encoding) # type: ignore[arg-type]
    elif name.endswith(Ext.lz4):
        import lz4.frame # type: ignore
        return lz4.frame.open(str(pp), mode, *args, **kwargs)
    elif name.endswith(Ext.zstd):
        return _zstd_open(pp, mode, *args, **kwargs)
    elif name.endswith(Ext.targz):
        import tarfile
        # FIXME pass mode?
        tf = tarfile.open(pp)
        # TODO pass encoding?
        x = tf.extractfile(*args); assert x is not None
        return x  #  type: ignore[return-value]
    else:
        return pp.open(mode, *args, **kwargs)


import typing
import os

if typing.TYPE_CHECKING:
    # otherwise mypy can't figure out that BasePath is a type alias..
    BasePath = pathlib.Path
else:
    BasePath = pathlib.WindowsPath if os.name == 'nt' else pathlib.PosixPath


class CPath(BasePath):
    """
    Hacky way to support compressed files.
    If you can think of a better way to do this, please let me know! https://github.com/karlicoss/HPI/issues/20

    Ugh. So, can't override Path because of some _flavour thing.
    Path only has _accessor and _closed slots, so can't directly set .open method
    _accessor.open has to return file descriptor, doesn't work for compressed stuff.
    """
    def open(self, *args, **kwargs):
        # TODO assert read only?
        return kopen(str(self))


open = kopen # TODO deprecate


# meh
# TODO ideally switch to ZipPath or smth similar?
# nothing else supports subpath properly anyway
def kexists(path: PathIsh, subpath: str) -> bool:
    try:
        kopen(path, subpath)
        return True
    except Exception:
        return False


import zipfile
class ZipPath(zipfile.Path):
    def absolute(self) -> ZipPath:
        return ZipPath(Path(self.root.filename).absolute(), self.at)

    def exists(self) -> bool:
        if self.at == '':
            # special case, the base class returns False in this case for some reason
            return Path(self.root.filename).exists()
        return super().exists()

    def rglob(self, glob: str) -> Sequence[ZipPath]:
        # note: not 100% sure about the correctness, but seem fine?
        # Path.match() matches from the right, so need to
        rpaths = [p for p in self.root.namelist() if p.startswith(self.at)]
        rpaths = [p for p in rpaths if Path(p).match(glob)]
        return [ZipPath(self.root, p) for p in rpaths]

    def relative_to(self, other: ZipPath) -> Path:
        assert self.root == other.root, (self.root, other.root)
        return Path(self.at).relative_to(Path(other.at))

    @property
    def __class__(self):
        return Path

    def __eq__(self, other) -> bool:
        # hmm, super class doesn't seem to treat as equals unless they are the same object
        if not isinstance(other, ZipPath):
            return False
        return self.root.filename == other.root.filename and self.at == other.at
