#!/usr/bin/env python
from __future__ import (absolute_import, print_function)

import os
import sys
import socket
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko import RSAKey
from paramiko.py3compat import u
from tempfile import NamedTemporaryFile
from runabove import Runabove


import logging.config

try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False

try:
    # on regarde si on a un fichier logging_dev.py qui est hors versionning
    from .logging_dev import LogConfig
except ImportError:
    from .logging_prod import LogConfig

logging.config.dictConfig(LogConfig.dictconfig)
logger = logging.getLogger(__name__)


class CourirSshException(Exception):
    pass


# thanks to demo from github paramiko project
class CourirSShInteractive(object):

    @staticmethod
    def interactive_shell(chan):
        if has_termios:
            CourirSShInteractive.posix_shell(chan)
        else:
            CourirSShInteractive.windows_shell(chan)

    @staticmethod
    def posix_shell(chan):
        import select

        oldtty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            chan.settimeout(0.0)

            while True:
                r, w, e = select.select([chan, sys.stdin], [], [])
                if chan in r:
                    try:
                        x = u(chan.recv(1024))
                        if len(x) == 0:
                            sys.stdout.write('\r\n*** EOF\r\n')
                            break
                        sys.stdout.write(x)
                        sys.stdout.flush()
                    except socket.timeout:
                        pass
                if sys.stdin in r:
                    x = sys.stdin.read(1)
                    if len(x) == 0:
                        break
                    chan.send(x)

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)

    @staticmethod
    def windows_shell(chan):
        import threading

        sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

        def writeall(sock):
            while True:
                data = sock.recv(256)
                if not data:
                    sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                    sys.stdout.flush()
                    break
                sys.stdout.write(data)
                sys.stdout.flush()

        writer = threading.Thread(target=writeall, args=(chan,))
        writer.start()

        try:
            while True:
                d = sys.stdin.read(1)
                if not d:
                    break
                chan.send(d)
        except EOFError:
            # user hit ^Z or F6
            pass


class CourirSsh(object):
    _region = 'SBG-1'
    _access_key_id = None
    _secret_access_key = None
    _consumer_key = None
    _key_path = None

    def __init__(self,
                 access_key_id,
                 secret_access_key,
                 consumer_key,
                 region='SBG-1',
                 key_path=os.getenv('HOME') + '/.ssh/',
                 log_level=None):
        """
        :param region: region used
        """
        if log_level is not None:
            logger.setLevel(log_level)
            logging.basicConfig(level=log_level)
        if region is not None:
            self._region = region

        self._key_path = key_path
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._consumer_key = consumer_key

    def list_ssh_key(self):
        """
        list ssh key on runabove
        :return:
        """
        runa = Runabove(
            self._access_key_id,
            self._secret_access_key,
            consumer_key=self._consumer_key)
        return runa.ssh_keys.list()

    def get_instances_by_name(self, name):
        """
        :param name:name of the instance you want to connect to
        :return: instance list
        """
        runa = Runabove(
            self._access_key_id,
            self._secret_access_key,
            consumer_key=self._consumer_key)
        instances = list()
        # let's list every single instance on runabove
        for i in runa.instances.list():
            if i.name == name:
                instances.append(i)

        return instances

    def connect(self, instance, ssh_user, ssh_ports, cmd, ssh_key_name):
        """
        execute a command on instance with ssh and return if cmd param is not None
        connect to ssh if cmd is None
        :param instance:
        :param ssh_user:
        :param ssh_ports:
        :param ssh_key_name:
        :param cmd: execute this command if not None
        :return:
        """

        # get instance public ip
        ssh_ip = instance.ip

        # we need to find the ssh key
        try:
            key_file = open(os.path.join(os.path.expanduser(self._key_path), ssh_key_name), 'r')
        except FileNotFoundError:
            try:
                key_file = open(os.path.join(os.path.expanduser(self._key_path), ssh_key_name + '.pem'), 'r')
            except FileNotFoundError:
                raise CourirSshException('private key %(key_name)s nor %(key_name)s.pem not found' % {
                    'key_name': ssh_key_name
                })

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        logger.debug('connecting to %s with port %s and user %s', ssh_ip, ssh_ports[0], ssh_user)
        mykey = RSAKey.from_private_key(key_file)

        # we try with each ssh_port we have
        for count, ssh_port in enumerate(ssh_ports):
            try:
                logger.debug(ssh_ip)
                logger.debug(ssh_port)
                client.connect(hostname=ssh_ip, port=int(ssh_port), username=ssh_user, pkey=mykey, timeout=4)
                if cmd is None:
                    with NamedTemporaryFile(mode='w+') as tmp_key_file:
                        mykey.write_private_key(tmp_key_file, password=None)
                        tmp_key_file.flush()
                        cmd = 'ssh -i %s %s@%s -p %s' % (tmp_key_file.name, ssh_user, ssh_ip, ssh_port)
                        logger.debug(cmd)
                        os.system(cmd)
                else:
                    stdin, stdout, stderr = client.exec_command(command=cmd)
                    out_str = stdout.read()
                    out_err = stderr.read().strip(' \t\n\r')
                    print(out_str)
                    if out_err != '':
                        print(out_err)
                        sys.exit(1)

            except (ConnectionRefusedError, socket.timeout):
                # we will try another tcp port
                if count < len(ssh_ports):
                    continue
                else:
                    raise CourirSshException('connection error')


