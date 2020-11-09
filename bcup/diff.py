"""
In this module there are functions that help analyze folders for differences.
There are also classes for File and Directory objects that a convenient to
use in sets inside of build_diff_map, so that is why it is necessary to
unpack the result to get the paths.
"""
import os
import filecmp
import tarfile
import logging

from . import utils


def copy_files(files, src, dst, dst_fs=None):
    """
    Copies files and folders represented as an iterable 'files' of file
    objects.
    """
    # Get relative paths of file objects
    paths = [file.path for file in files]

    # Sorting paths to ensure folders come before internal files
    paths.sort()

    # Copy loop
    for path in paths:
        src_path = os.path.join(src, path)
        dst_path = os.path.join(dst, path)

        # Skip file with forbidden path
        if dst_fs is not None and not dst_fs.is_path_allowed(dst):
            continue

        # Ensure parent directory
        utils.ensure_dir(os.path.dirname(dst_path))

        if os.path.islink(src_path) or os.path.isfile(src_path):
            # Copy file or symlink
            utils.copy_file(src_path, dst_path)

        elif os.path.isdir(src_path):
            # Create empty directory
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)

        else:
            logging.warning(f"Unknown type of file: {src_path}")


def remove_files(files, root):
    """
    Removes files and folders represented as an iterable 'files' of file
    objects.
    """
    # Extract paths from file objects 'files'
    abs_paths = [
        os.path.join(root, file.path)
        for file in files
    ]

    # Reverse sorting abs_paths. It is needed to remove internal files first
    # before the containing folder. So the folder will be empty on remove,
    # if it must be removed.
    abs_paths.sort(reverse=True)

    # Removing
    for path in abs_paths:
        if os.path.lexists(path):
            if os.path.islink(path):
                # Remove symlink
                os.unlink(path)

            elif os.path.isfile(path):
                # Remove regular file
                os.remove(path)

            elif os.path.isdir(path):
                # Remove folder if it is not empty
                if not os.listdir(path):
                    os.rmdir(path)

            else:
                logging.warning(f"Unknown type of file: {path}")

        else:
            logging.warning(f"Path does not exist: {path}")


def unpack_files(files):
    """
    Returns a list of paths of given file objects.
    """
    return [file.path for file in files]


def collect_paths(root):
    """
    Collects paths of all files and folder in the directory 'root'.
    """
    files = set()

    for dirpath, dirnames, filenames in os.walk(root):
        rel_root = os.path.relpath(dirpath, root)

        # Process folders. There can be symlinks among the scanning folders.
        for name in dirnames:
            full_path = os.path.join(dirpath, name)

            if os.path.islink(full_path):
                file_cls = Symlink
            elif os.path.isdir(full_path):
                file_cls = Directory
            else:
                continue

            path = os.path.normpath(os.path.join(rel_root, name))
            files.add(file_cls(path))

        # Process files. There can be symlinks among the scanning files.
        for name in filenames:
            full_path = os.path.join(dirpath, name)

            if os.path.islink(full_path):
                file_cls = Symlink
            elif os.path.isfile(full_path):
                file_cls = File
            else:
                continue

            path = os.path.normpath(os.path.join(rel_root, name))
            files.add(file_cls(path))

    return files


def collect_paths_in_tar(tar_path):
    """
    Collects paths of all files and folder in tar archive in 'tar_path'.
    """
    files = set()
    with tarfile.open(tar_path, 'r:gz') as tar:
        for member in tar.getmembers():
            if '/' in member.name:
                path = member.name.split('/', 1)[1]
            else:
                continue
            if member.issym():
                files.add(Symlink(path))
            elif member.isdir():
                files.add(Directory(path))
            else:
                files.add(File(path))
    return files


def filter_changed_files(files, path1, path2):
    """
    Filter 'files' to get a set of distinct files only in 'path1' and 'path2'.
    """
    filtered = set()

    for file in files:
        if isinstance(file, File):
            if not filecmp.cmp(
                os.path.join(path1, file.path),
                os.path.join(path2, file.path),
            ):
                filtered.add(file)

        elif isinstance(file, Symlink):
            target1 = os.readlink(os.path.join(path1, file.path))
            target2 = os.readlink(os.path.join(path2, file.path))
            if target1 != target2:
                filtered.add(file)

    return filtered


def filter_changed_files_in_tar(files, dir_path, tar_path):
    """
    Filter 'files' to get a set of distinct files only in folder 'dir_path' and
    tar archive 'tar_path'.
    """
    filtered = set()

    with tarfile.open(tar_path, 'r:gz') as tar:
        # Getting root
        root = tar.next().name
        if '/' in root:
            root = root.split('/', 1)[0]

        # Loop throught given files
        for file in files:
            # If File
            if isinstance(file, File):
                # Open file
                path = os.path.join(dir_path, file.path)
                fileobj1 = open(path, 'rb')

                # Get file from tar
                name = os.path.join(root, file.path)
                member = tar.getmember(name)
                fileobj2 = tar.extractfile(member)

                # If contents are no equal, add to filtered
                if not _compare_file_objects(fileobj1, fileobj2):
                    filtered.add(file)

                # Close file objects
                fileobj1.close()
                fileobj2.close()

            # If Symlink
            elif isinstance(file, Symlink):
                path = os.path.join(dir_path, file.path)
                target1 = os.readlink(path)

                name = os.path.join(root, file.path)
                member = tar.getmember(name)
                target2 = member.linkname

                if target1 != target2:
                    filtered.add(file)

    return filtered


def _compare_file_objects(fileobj1, fileobj2, chunk_size=10000):
    fileobj1.seek(0)
    fileobj2.seek(0)
    while True:
        chunk1 = fileobj1.read(chunk_size)
        chunk2 = fileobj2.read(chunk_size)
        if chunk1 != chunk2:
            return False
        if not chunk1 and not chunk2:
            break
    return True


class BaseFile:
    """
    BaseFile implements a file object that can be compared and hashed, so
    in can be used in sets.
    """
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path})"

    def __hash__(self):
        return hash(self.path) + hash(self.__class__)

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.path == other.path


class File(BaseFile):
    """
    File type of file object.
    """
    pass


class Symlink(BaseFile):
    """
    Symlink type of file object.
    """
    pass


class Directory(BaseFile):
    """
    Directory type of file object.
    """
    def __init__(self, path):
        super().__init__(path)
        self._ensure_trailing_slash()

    def _ensure_trailing_slash(self):
        """
        Ensures the trailing slash in path for folders always.
        """
        if not self.path.endswith(os.sep):
            self.path += os.sep
