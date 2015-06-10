import click
from click import UsageError

import logging
import os
import sys

try:
    import configparser
    from configparser import NoOptionError
except ImportError:
    import ConfigParser as configparser
    from ConfigParser import NoOptionError

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

        # we need the config file
        try:
            config = configparser.ConfigParser()
            config.read_file(open(configfile))

            access_key_id = config.get('runabove', 'access_key_id')
            if access_key_id is None or len(access_key_id) == 0:
                raise UsageError('access_key_id not found in %s' % configfile)

            secret_access_key = config.get('runabove', 'secret_access_key')
            if secret_access_key is None or len(secret_access_key) == 0:
                raise UsageError('secret_access_key not found in %s' % configfile)

            ssh_user = config.get('runabove', 'ssh_user')
            ssh_port = config.get('runabove', 'ssh_port')
        except IOError:
            raise UsageError('%s config file not found' % configfile)
        except configparser.NoSectionError:
            raise UsageError('section %s not found in config file %s' % ('runabove', configfile))
