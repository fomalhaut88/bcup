"""
The purpose of this module is to determine if a path is valid under the target
file system (for copy a file, for example).
"""
import os

import psutil


class BaseFs:
    """
    Base class for file system object.
    """
    # Characters that are forbidden for names (taken from
    # https://en.wikipedia.org/wiki/Filename)
    forbidden_chars = ''

    def is_path_allowed(self, path):
        """
        Returns True if all names in path are valid.
        """
        return all(map(self.is_name_allowed, path.split(os.sep)))

    def is_name_allowed(self, name):
        """
        Checks the name for forbidden characters.
        """
        return not any(map(name.__contains__, self.forbidden_chars))


class Ntfs(BaseFs):
    """
    System NTFS
    """
    forbidden_chars = r'"*/:<>?\|'


class Fat32(BaseFs):
    """
    System FAT32
    """
    forbidden_chars = r'"*/:<>?\|+,.;=[]'


class Ext4(BaseFs):
    """
    System POSIX
    """
    forbidden_chars = r'/'


# Mapping from partition fstype (from psutil.sdiskpart tuple)
# to file system class
FS_MAP = {
    'ext4': Ext4,
    'fuseblk': Ntfs,
    'vfat': Fat32,
}


def determine_fs(path):
    """
    Tries to determine the file system by path.
    It returns a file system object.
    """
    root_part = None
    found_part = None

    for part in psutil.disk_partitions():
        if part.mountpoint == '/':
            root_part = part

        if path == part.mountpoint or \
                path.startswith(part.mountpoint + os.sep):
            found_part = part
            break

    if found_part is None:
        found_part = root_part

    if found_part is not None:
        fs_class = FS_MAP[found_part.fstype]
        return fs_class()
    else:
        raise OSError(f"Could not determine file system for path: {path}")
