"""
There are some general useful functions.
"""
import os
import shutil
import tarfile

import yaml


def copy_file(src, dst, dst_fs=None):
    """
    Copies file or symlink from 'src' to 'dst'.
    """
    if dst_fs is None or dst_fs.is_path_allowed(dst):
        shutil.copy2(src, dst, follow_symlinks=False)


def copy_tree(src, dst, dst_fs=None):
    """
    Copies folder with files inside.
    """
    if dst_fs is not None and not dst_fs.is_path_allowed(dst):
        return

    os.mkdir(dst)

    for name in os.listdir(src):
        src_sub = os.path.join(src, name)
        dst_sub = os.path.join(dst, name)

        if os.path.isdir(src_sub):
            if os.path.islink(src_sub):
                copy_file(src_sub, dst_sub, dst_fs=dst_fs)
            else:
                copy_tree(src_sub, dst_sub, dst_fs=dst_fs)
        else:
            copy_file(src_sub, dst_sub, dst_fs=dst_fs)


def rm_tree(path):
    """
    Removes folder with files inside.
    """
    shutil.rmtree(path)


def ensure_dir(path):
    """
    If makes directories chain given in path and does nothing if they exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def load_yaml(path):
    """
    Loads a YAML config by path.
    """
    with open(path) as f:
        return yaml.load(f, Loader=yaml.Loader)


def save_yaml(path, config):
    """
    Saves a YAML config by path.
    """
    with open(path, 'w') as f:
        yaml.dump(config, f)


def tar_compress(path, tar_path, root=None):
    """
    Creates tar archive for the folder given as 'path'.
    """
    assert tar_path.endswith('.tar.gz'), f"Invalid extension: {tar_path}"
    folder = root if root else os.path.basename(path)
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add(path, folder)


def tar_decompress(target, tar_path):
    """
    Extracts from tar archive into 'target'.
    """
    assert tar_path.endswith('.tar.gz'), f"Invalid extension: {tar_path}"
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(target)
