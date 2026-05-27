import os
import configobj
from validate import Validator
from configobj import ConfigObj

__here__ = os.path.abspath(os.path.dirname(__file__))


def parse_config() -> ConfigObj:
    """
    This returns a parsed ConfigObj for our config using three files:
    1) chargen/configspec.ini is our spec file which defines which options exist
    2) development-defaults.ini has the default values which we check into git
    3) development-secrets.ini is where we store sensitive values like passwords
    """
    specfile = os.path.join(__here__, 'configspec.ini')
    spec = ConfigObj(
        specfile, interpolation=False, list_values=False, encoding='utf-8', _inspec=True
    )

    development_defaults_fpath = os.path.abspath(
        os.path.join(__here__, '..', 'development-defaults.ini')
    )
    development_secrets_fpath = os.path.abspath(
        os.path.join(__here__, '..', 'development-secrets.ini')
    )

    config = ConfigObj(development_defaults_fpath, encoding='utf-8', configspec=spec)
    config.merge(ConfigObj(development_secrets_fpath, encoding='utf-8', configspec=spec))

    validation = config.validate(Validator(), preserve_errors=True)
    if validation is not True:
        raise ValueError(
            f'configuration validation error(s): {configobj.flatten_errors(config, validation)}'
        )

    return config


config = parse_config()

from chargen._version import __version__
import chargen.website
