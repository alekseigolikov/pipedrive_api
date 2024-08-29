#!/usr/bin/python3
import logging
import argparse
import sys
import datetime
import os

from modules.pipedriveapi import PipedriveREST, PipedriveCLI
from modules.keyvault import KeyVaultStorage
from modules.file_import import FileLoad

# logging format
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
home = os.path.expanduser('~')

commands = """

PipedriveCLI admin:
    fetch_token             fetch initial token
    refresh_token           request token refresh and store it
    whoami                  request information of token owner
    deals                   list all dealst

KeyVaultStorage admin:
    get_auth                Show auth related values
    set_auth                Set auth related values


"""

cmd_handlers = (
    (('fetch_token', 'refresh_token', 'whoami', 'deals'), PipedriveCLI),
    (('get_auth', 'set_auth'), KeyVaultStorage),
    (('load_file'), FileLoad)
)


class PipeDrive(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            usage='''pipedrive.py <command> [<args>]

Available commands are:
%s''' % commands)

        parser.add_argument('command', help='Subcommand to run')
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[1:2])

        command = args.command

        # setup logging
        t = datetime.datetime.now()
        t = t.strftime("%y%m%d_%H%M%S%f")

        # logfile will be written to users home dir log dir
        lf = '%s/log/%s_%s.log' % (home, command, t)

        # create log directory if it doesn't exist
        if not os.path.exists(os.path.dirname(lf)):
            os.makedirs(os.path.dirname(lf))

        logFormatter = logging.Formatter(FORMAT)
        rootLogger = logging.getLogger()

        # to file
        fileHandler = logging.FileHandler(lf)
        fileHandler.setFormatter(logFormatter)
        # into file everitying goes always on debug level
        fileHandler.setLevel(logging.DEBUG)
        rootLogger.addHandler(fileHandler)

        # to console
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        # set loglevel for console
        if '-v' in sys.argv or '--verbose' in sys.argv:
            consoleHandler.setLevel(logging.DEBUG)
        else:
            consoleHandler.setLevel(logging.INFO)
        rootLogger.addHandler(consoleHandler)
        # handlers can have messages only if rootlogger has them
        rootLogger.setLevel(5)

        # run command
        c = None
        command_list = []
        for cmd_names, handler_class in cmd_handlers:
            if command in cmd_names:
                c = handler_class()
                logging.info("Starting %s" % command)
                logging.debug("Executed command: %s" % ' '.join(sys.argv))
                logging.info("Logfile: %s" % lf)
                getattr(c, command)()
                logging.info("Finished %s" % command)
                break
            command_list += cmd_names
        if command == 'commands':
            print((" ".join(command_list)))
        elif not c:
            print(("Unknown command '%s', use --help for help" % command))
            sys.exit(1)

        return


if __name__ == "__main__":
    PipeDrive()
