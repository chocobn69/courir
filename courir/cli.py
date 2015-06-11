import click
from click import UsageError

from .ssh import CourirSsh, CourirSshException

import logging.config
import os
import sys
from runabove import Runabove

import configparser

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
    @click.option('--name', '-n', required=True, multiple=False, help='instance name where you want to connect to')
    @click.option('--configfile', '-c', default=os.getenv('HOME') + '/.courir', help='config file for courir '
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
            ssh_ports = config.get('runabove', 'ssh_ports').split(',')

            try:
                consumer_key = config.get('runabove', 'consumer_key')
            except configparser.NoOptionError:
                consumer_key = None
            if consumer_key is None or len(consumer_key) == 0:
                # we don't have a consumer yet, let's generate one
                # Create an instance of Runabove SDK interface
                run = Runabove(access_key_id, secret_access_key)

                # Request an URL to securely authenticate the user
                print("You should login here: %s" % run.get_login_url())
                input("When you are logged, press Enter")

                # Show the consumer key
                print("Your consumer key is: %s" % run.get_consumer_key())
                print("Please report this key to your config file : %s" % configfile)
                sys.exit(0)

            try:
                region = config.get('runabove', 'region')
            except configparser.NoOptionError:
                region = 'SBG-1'

            try:
                key_path = config.get('runabove', 'key_path')
            except configparser.NoOptionError:
                key_path = '~/.ssh/'

        except IOError:
            raise UsageError('%s config file not found' % configfile)
        except configparser.NoOptionError as e:
            raise UsageError('%s in config file %s' % (e, configfile))
        except configparser.NoSectionError:
            raise UsageError('section %s not found in config file %s' % ('runabove', configfile))

        # now we can try to connect
        try:
            ssh = CourirSsh(access_key_id=access_key_id,
                            secret_access_key=secret_access_key,
                            consumer_key=consumer_key,
                            region=region,
                            key_path=key_path,
                            log_level=logger.getEffectiveLevel())
            instances = ssh.get_instances_by_name(name)
            # if we have more than one instance, we need to make a choice
            if len(instances) > 1:
                count_instance = 1
                click.echo('0) None, I will filter more')
                for instance in instances:
                    click.echo('%s) %s - %s' % (count_instance,
                                                instance.id,
                                                instance.ip))
                    count_instance += 1
                choosen_one = int(click.prompt('Please choose an instance', type=int))
                if choosen_one < 0 or choosen_one > len(instances):
                    raise UsageError('You have to choose a correct instance'
                                     ' between %s and %s' % (1, len(instances)))
            # if we have one instance only
            elif len(instances) == 1:
                choosen_one = 1
            # if we have no instance at all
            else:
                raise UsageError('Name %s not found' % (name, ))

            if choosen_one == 0:
                sys.exit(0)

            instance_chosen = instances[choosen_one - 1]
            ssh_key_name = instance_chosen.ssh_key.name

            return ssh.connect(instance=instance_chosen,
                               ssh_user=ssh_user,
                               ssh_ports=ssh_ports,
                               ssh_key_name=ssh_key_name,
                               cmd=execute)

        except CourirSshException as e:
            raise UsageError(str(e))
