from glob import glob
import json
from os import walk
from shutil import rmtree
from tempfile import mkdtemp
from typing import Optional
from zipfile import ZipFile
from pathlib import Path

class VirtualDir:
    def __init__(self, extension: Optional[str] = None) -> None:
        """
        Args:
            extension: The zip archive extension name including the initial dot
            (if the content files are `load`ed or `archive`d to a zip archive).
        """
        self._files: dict[str, Optional[bytes]] = {}
        self._extension = extension

    def get_file(self, rpath: str) -> Optional[bytes]:
        return self._files[rpath]

    def set_file(self, rpath: str, content: bytes | str) -> None:
        if isinstance(content, str):
            content = content.encode("utf8")
        self._files[rpath] = content

    def remove_file(self, rpath: str) -> None:
        del self._files[rpath]

    def load(self, path: str | Path) -> None:
        """
        Load files from a directory or a zip archive.
        Args:
            path: The path to the directory or zip archive. If `extension` is
            not `None` and `path` points to a zip archive, `path` must ends with
            the given extension name.
        """
        if isinstance(path, str):
            path = Path(path)
        # Ensure the directory exists.
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_file() and path.name.endswith('.tcm'):
            # Load files from a zip archive.
            with ZipFile(path, "r") as z:
                for rpath in z.namelist():
                    assert rpath not in self._files
                    data = z.read(rpath)
                    self._files[rpath] = data
        else:
            # Load files from the filesystem.
            for dir, dname, fname in walk(path):
                for f in fname:
                    rpath = Path(dir) / f
                    assert rpath not in self._files
                    with open(rpath, "rb") as f:
                        rpath = rpath.relative_to(path)
                        data = f.read()
                        self._files[str(rpath)] = data

    def save(self, path: str | Path):
        """
        Save files to a directory.
        Args:
            path: The path to the directory. If the directory doesn't exist, it
            will be created with all parent directories.
        """
        if isinstance(path, str):
            path = Path(path)
        # Make sure the directory exists.
        if not path.exists():
            path.mkdir(parents=True)
        # Write files directly to the filesystem.
        assert path.is_dir()
        for rpath in self._files:
            data = self._files[rpath]
            assert data is not None
            with open(path / rpath, "wb") as f:
                f.write(data)

    def archive(self, path: str | Path):
        """
        Archive files to a zip archive.
        Args:
            path: The path to the zip archive. If `extension` is not `None`, the
            path must ends with the given extension name.
        """
        if isinstance(path, str):
            path = Path(path)
        assert path.name.endswith(".tcm"), \
            "AOT module artifact archive must ends with .tcm"
        tcm_path = Path(path).absolute()
        assert tcm_path.parent.exists(), "Output directory doesn't exist"

        temp_dir = mkdtemp(prefix="tcm_")
        # Save first as usual.
        self.save(temp_dir)

        # Package all artifacts into a zip archive and attach contend data.
        with ZipFile(tcm_path, "w") as z:
            for path in glob(f"{temp_dir}/*", recursive=True):
                z.write(path, Path.relative_to(Path(path), temp_dir))

        # Remove cached files
        rmtree(temp_dir)
