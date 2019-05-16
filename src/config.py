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

    config: str
    wallet: str
    inbound_transport: str
    outbound_transport: str
    log_level: int

    def __init__(self):
        self.config: str = None
        self.wallet: str = None
        self.inbound_transport: str = None
        self.outbound_transport: str = None
        self.log_level: int = None

    @staticmethod
    def default_options():
        return {
            'wallet': 'agent',
            'inbound_transport': 'stdin',
            'outbound_transport': 'stdout',
            'log_level': 10
        }

    @staticmethod
    def get_arg_parser():
        """ Construct an argument parser that matches our configuration.
        """
        parser = argparse.ArgumentParser(
            description='Agent',
            prog='agent'
        )
        parser.add_argument(
            '-c',
            '--config',
            dest='config',
            metavar='FILE',
            type=str,
            help='Load configuration from FILE.'
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

    def load_options_from_file(self, config_path: str):
        options = toml.load(config_path)
        self.update(options, soft=True)


    @staticmethod
    def from_file(config_path: str):
        """ Create config object from toml file.
        """
        conf = Config()
        conf.load_options_from_file(config_path)
        return conf

    @staticmethod
    def from_args_file_defaults():
        conf = Config()
        parser = Config.get_arg_parser()
        parser.parse_known_args(namespace=conf)
        if conf.config:
            conf.load_options_from_file(conf.config)

        conf.update(Config.default_options(), soft=True)
        return conf

    def update(self, options: Dict[str, Any], **kwargs):
        """ Load configuration from the options dictionary.
        """
        soft = 'soft' in kwargs and kwargs['soft']

        for var in self.__dict__:
            if var in options and options[var] is not None:
                if not isinstance(options[var], Config.__annotations__[var]):
                    err_msg = 'Configuration option {} is an invalid type'.format(var)
                    raise InvalidConfigurationException(err_msg)

                if soft:
                    if self.__dict__[var] is None:
                        self.__dict__[var] = options[var]
                else:
                    self.__dict__[var] = options[var]


if __name__ == '__main__':

    print("TESTING CONFIGURATION")
    CONFIG = Config.from_args_file_defaults()
    print(CONFIG.__dict__)
