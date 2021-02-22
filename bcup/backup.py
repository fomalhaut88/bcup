"""
It contains the internal logic of backups. Generally backup is an entity
that can be created and made with the result as stored new data and in
some cases cleaned old stored backup data.

Use create_backup_from_source to create correctly a backup object
from the known source. Backup class is generated dynamically from mixins
according to given method (full, last, diff).
"""
import re
import os
from datetime import datetime

from . import utils, diff


def create_backup_from_source(source):
    """
    Creates a backup object from the source according to source.method.
    """
    if source.method == 'full':
        backup_cls = type('MethodFullBackup',
                          (PlainCopyMixin, FullExtraMixin, BaseBackup), {})
    elif source.method == 'last':
        backup_cls = type('MethodLastBackup',
                          (PlainCopyMixin, LastExtraMixin, BaseBackup), {})
    elif source.method == 'diff':
        backup_cls = type('MethodDiffBackup',
                          (DiffCopyMixin, FullExtraMixin, BaseBackup), {})
    else:
        raise ValueError(source.method)
    return backup_cls(source)


class BaseBackup:
    """
    An abstract class for backup objects.
    """
    # The name of directory for backuped data
    data_dir = 'data'

    # The name of info file
    info_file = 'info'

    def __init__(self, source):
        self.source = source

    def make(self):
        """
        Makes backup.
        """
        self._prepare()
        self._build_diff_map()
        if self._has_changes():
            utils.ensure_dir(self.path)
            self._copy_data()
            self._save_info()
            self._remove_extra()

    def _build_diff_map(self):
        """
        Calculates difference map between the last backup and
        the source. The result will be stored into self.diff_map.
        """
        # Get all paths in source folder
        paths = diff.collect_paths(self.source.source)

        # Filter allowed paths for copying
        paths = set(filter(
            lambda file: self.source.target_fs.is_path_allowed(file.path),
            paths
        ))

        # Get last key
        last_key = self._get_last_key()

        if last_key is not None:
            last_data_path = os.path.join(self.source.path, last_key,
                                          self.data_dir)

            # Use different logic for compressed data.
            # Notice: we do not compress the last backup if source.method
            # is 'diff' in order to increase the preformance.
            if self.source.compress and self.source.method != 'diff':
                self.diff_map = self._create_diff_map_in_tar(last_data_path,
                                                            paths)

            else:
                self.diff_map = self._create_diff_map(last_data_path, paths)

        else:
            # If no previous backup found, fill 'added' key only
            self.diff_map = {
                'added': paths,
                'removed': set(),
                'changed': set(),
                'same': set(),
            }

    def _create_diff_map(self, last_data_path, paths):
        """
        Builds diff_map.
        """
        # Extract all paths from last backup
        last_paths = diff.collect_paths(last_data_path)

        # Calculate differences
        added = paths - last_paths
        removed = last_paths - paths
        similar = last_paths & paths
        changed = diff.filter_changed_files(
            similar, self.source.source, last_data_path
        )
        same = similar - changed

        return {
            'added': added,
            'removed': removed,
            'changed': changed,
            'same': same,
        }

    def _create_diff_map_in_tar(self, last_data_path, paths):
        """
        Builds diff_map with archived last_data_path.
        """
        # Extract all paths from tar archive
        last_paths = diff.collect_paths_in_tar(
            last_data_path + '.tar.gz'
        )

        # Calculate differences
        added = paths - last_paths
        removed = last_paths - paths
        similar = last_paths & paths
        changed = diff.filter_changed_files_in_tar(
            similar, self.source.source, last_data_path + '.tar.gz'
        )
        same = similar - changed

        return {
            'added': added,
            'removed': removed,
            'changed': changed,
            'same': same,
        }

    def _has_changes(self):
        """
        Returns True if self.diff_map contains any differences.
        """
        return bool(self.diff_map['added']) or \
               bool(self.diff_map['removed']) or \
               bool(self.diff_map['changed'])

    def _get_last_key(self, depth=1):
        """
        Gets key of previous backups in 'depth' backward.
        """
        if os.path.exists(self.source.path):
            keys = os.listdir(self.source.path)
            keys.sort()
            return keys[-depth] if len(keys) >= depth else None
        else:
            return None

    def _prepare(self):
        """
        Prepares the necessary attributes.
        """
        self.dt = datetime.now()
        self.key = self._build_key(self.source.fmt, self.dt)
        self.path = os.path.join(self.source.path, self.key)
        self.data_path = os.path.join(self.path, self.data_dir)
        self.info_path = os.path.join(self.path, self.info_file)

    @classmethod
    def _build_key(cls, fmt, dt):
        """
        Builds key (the name of backup folder) according to given datetime
        and the format.
        """
        py_fmt = re.sub(r'([YymdHMSf])', r'%\1', fmt)
        return dt.strftime(py_fmt)

    def _prepare_info(self):
        """
        Creates info config for the backup.
        """
        return {
            'dt': self.dt.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'key': self.key,
            'added': diff.unpack_files(self.diff_map['added']),
            'removed': diff.unpack_files(self.diff_map['removed']),
            'changed': diff.unpack_files(self.diff_map['changed']),
        }

    def _save_info(self):
        """
        Saves the info file.
        """
        info = self._prepare_info()
        utils.save_yaml(self.info_path, info)

    def _copy_data(self):
        """
        It contains the logic of copying the data.
        """
        raise NotImplementedError()

    def _remove_extra(self):
        """
        It contains the logic to clean olf backup files.
        """
        raise NotImplementedError()


class PlainCopyMixin:
    """
    It implements copying the full directory and compressing if needed.
    """
    def _copy_data(self):
        if self.source.compress:
            # Create tar archive
            utils.tar_compress(self.source.source, self.data_path + '.tar.gz',
                               root=self.data_dir)
        else:
            # Copy data from source to backup
            utils.copy_tree(self.source.source, self.data_path,
                            dst_fs=self.source.target_fs)


class DiffCopyMixin:
    """
    If implements copying of changes in the source, so in backups changed
    and removed files and folders are stored.
    """
    def _copy_data(self):
        # Get key of previous backup. We use depth=2, because the folder
        # for this backup already created (on utils.ensure_dir(self.path) step)
        # in make(self).
        prev_key = self._get_last_key(depth=2)

        if prev_key:
            prev_path = os.path.join(self.source.path, prev_key)
            prev_data_path = os.path.join(prev_path, self.data_dir)

            # Move data from previous backup to current one
            os.rename(prev_data_path, self.data_path)

            # Create empty directory for previous backup after moving
            os.mkdir(prev_data_path)

            # Copy changed and removed files to previous backup
            diff.copy_files(self.diff_map['changed'], self.data_path,
                            prev_data_path, dst_fs=self.source.target_fs)
            diff.copy_files(self.diff_map['removed'], self.data_path,
                            prev_data_path, dst_fs=self.source.target_fs)

            # Copy added and changed files from source, remove removed files
            diff.copy_files(self.diff_map['added'], self.source.source,
                            self.data_path, dst_fs=self.source.target_fs)
            diff.copy_files(self.diff_map['changed'], self.source.source,
                            self.data_path, dst_fs=self.source.target_fs)
            diff.remove_files(self.diff_map['removed'], self.data_path)

            # Create tar archive and remove related directory
            if self.source.compress:
                utils.tar_compress(prev_data_path, prev_data_path+ '.tar.gz',
                                   root=self.data_dir)
                utils.rm_tree(prev_data_path)

        else:
            # Copy data from source to backup
            utils.copy_tree(self.source.source, self.data_path,
                            dst_fs=self.source.target_fs)


class LastExtraMixin:
    """
    It implements the remove every backup file except for the current one.
    """
    def _remove_extra(self):
        for key in os.listdir(self.source.path):
            if key != self.key:
                path = os.path.join(self.source.path, key)
                utils.rm_tree(path)


class FullExtraMixin:
    """
    It implements the remove of all backup files except for a fixed number
    (limit, it represents in self.source) of newest backups.
    """
    def _remove_extra(self):
        if self.source.limit:
            keys = os.listdir(self.source.path)
            if len(keys) > self.source.limit:
                keys.sort()
                keys_to_remove = keys[:len(keys) - self.source.limit]
                for key in keys_to_remove:
                    path = os.path.join(self.source.path, key)
                    utils.rm_tree(path)
