import click
from click import UsageError

import logging
import os
import sys

try:
    from .logging_dev import LogConfig
except ImportError:
    from .logging_prod import LogConfig

logging.config.dictConfig(LogConfig.dictconfig)
logger = logging.getLogger(__name__)

class CourirCliException(Exception):
    pass

class Cli(object):

    @staticmethod
    @click.command()
    @click.option('--name', '-n', multiple=True, help='instance name where you want to connect to')
    @click.option('--configfile', '-c', default=os.getenv('HOME') + '/.sergent', help='config file for courir '
                                                                                      '(default ~/.courir)')
    @click.option('--debug/--no-debug', default=False, help='turn on debug (default False)')
    @click.option('--execute', '-e', default=None, help='execute cmd (default, None)')
    def go(name, configfile, debug, execute):
        # turn on debug mode (mainly for boto)
        if debug is True:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)
            logger.setLevel(logging.ERROR)
