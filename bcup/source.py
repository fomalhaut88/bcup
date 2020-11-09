"""
Source object is a struct with necessary attributes to determine everything
that is needed to create and make backups for a certain source.
"""
import os

from .filesystem import determine_fs


class Source:
    def __init__(self, name, fmt, source, target, period, method='full',
                 compress=False, limit=None):
        self.name = name
        self.fmt = fmt
        self.source = source
        self.target = target
        self.period = period
        self.method = method
        self.compress = compress
        self.limit = limit
        self.path = os.path.join(target, name)
        self.target_fs = determine_fs(target)

    @classmethod
    def from_config_params(cls, params, fmt):
        """
        Create a source object from params given as a dictionary.
        Name will be calculated from the given source path according to
        the method _build_name.
        """
        name = cls._build_name(params['source'])
        return cls(name, fmt=fmt, **params)

    @classmethod
    def _build_name(cls, source):
        """
        It creates a name of source that is readable and unique for each
        directory.
        """
        name = source.replace('/', '_')
        return name
