import os
import logging

from bcup import utils
from bcup.source import Source
from bcup.manager import Manager


# Read config path from CONFIG_PATH environment variable, default is config.yml
CONFIG_PATH = os.environ.get('CONFIG_PATH', 'config.yml')

# Set log level from environment variable
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


if __name__ == "__main__":
    # Set log level
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Load config
    config = utils.load_yaml(CONFIG_PATH)

    # Create manager
    manager = Manager()

    for params in config['sources']:
        # Create a source object from params in config
        source = Source.from_config_params(params, config['format'])

        # Add the source object to the manager
        manager.add(source)

    # Run backups
    manager.run()
