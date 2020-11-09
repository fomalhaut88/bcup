import os

from bcup import utils
from bcup.source import Source
from bcup.backup import create_backup_from_source


# Read config path from BCUP_CONFIG environment variable, default is config.yml
CONFIG_PATH = os.environ.get('BCUP_CONFIG', 'config.yml')


if __name__ == "__main__":
    # Load config
    config = utils.load_yaml(CONFIG_PATH)

    for params in config['sources']:
        # Create a source object from params in config
        source = Source.from_config_params(params, config['format'])

        # Create a backup object
        backup = create_backup_from_source(source)

        # Make backup
        backup.make()
