""" Module for storing and updating configuration.
"""

import argparse
from typing import Dict, Any
import toml


class InvalidConfigurationException(Exception):
    """ Exception raise on absent required configuration value
    """


class Config:
    """ Configuration class used to store and update configuration information.
    """

    @staticmethod
    def get_arg_parser():
        """ Construct an argument parser that matches our configuration.
        """
        parser = argparse.ArgumentParser(
            description='Agent',
            prog='agent'
        )
        parser.add_argument(
            '-i',
            '--inbound-transport',
            dest='inbound_transport',
            metavar='INBOUND_TRANSPORT',
            type=str,
            help='Set the inbound transport type.'
        )
        parser.add_argument(
            '-o',
            '--outbound-transport',
            dest='outbound_transport',
            metavar='OUTBOUND_TRANSPORT',
            type=str,
            help='Set the outbound transport type.'
        )
        parser.add_argument(
            '-w',
            '--wallet',
            dest='wallet',
            metavar='WALLET',
            type=str,
            help='Specify wallet'
        )
        return parser

    @staticmethod
    def from_file(config_path: str):
        """ Create config object from toml file.
        """
        conf = Config()
        options = toml.load(config_path)
        conf.update(options)
        return conf

    def __init__(self):
        self.wallet: str = 'agent'
        self.inbound_transport: str = "stdin"
        self.outbound_transport: str = "stdout"
        self.log_level: int = 10

    def update(self, options: Dict[str, Any]):
        """ Load configuration from the options dictionary.
        """

        for var in self.__dict__:
            if var in options and options[var] is not None:
                if type(options[var]) is not type(self.__dict__[var]):
                    err_msg = 'Configuration option {} is an invalid type'.format(var)
                    raise InvalidConfigurationException(err_msg)

                self.__dict__[var] = options[var]

if __name__ == '__main__':

    DEFAULT_CONFIG_PATH = 'config.sample.toml'

    print("TESTING CONFIGURATION")
    PARSER = Config.get_arg_parser()
    CONFIG = Config.from_file(DEFAULT_CONFIG_PATH)

    PARSER.parse_known_args(namespace=CONFIG)

    print(CONFIG.__dict__)
