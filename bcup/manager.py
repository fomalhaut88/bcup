"""
Manager is a class that implements running backups according to their periods.
"""
import logging
import traceback
from time import time, sleep

from .backup import create_backup_from_source


TIMEOUT = 1.0


class Manager:
    def __init__(self):
        self._source_map = {}
        self._run_map = {}

    def add(self, source):
        """
        Adds source into _source_map
        """
        assert source.name not in self._source_map
        self._source_map[source.name] = source
        self._run_map[source.name] = None

    def run(self):
        """
        Run backups as an infinite loop. At each iteration it checks the
        passed time from last run before making a new backup.
        """
        # Start backup loop
        while True:
            for source in self._source_map.values():
                # If the period passed
                if self._is_ready(source):
                    try:
                        logging.info(f"Start backup for {source.name}")

                        # Create backup object
                        backup = create_backup_from_source(source)

                        # Make backup
                        backup.make()

                        logging.info(f"Completed backup for {source.name}")

                    except:
                        logging.error(traceback.format_exc())

                    finally:
                        self._run_map[source.name] = time()

            # Sleep before next check
            sleep(TIMEOUT)

    def _is_ready(self, source):
        """
        Returns True, if the period passed from the last run. Else False.
        """
        last = self._run_map[source.name]
        return last is None or time() > last + source.period
