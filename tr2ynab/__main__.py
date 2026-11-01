# pylint: disable=missing-module-docstring,missing-function-docstring
from argparse import ArgumentParser
import logging
import os
from tr2ynab import ynab_push_transactions, tr_load_transactions
from tr2ynab.tr2ynab import Settings
from ._version import __version__


def main():
    parser = ArgumentParser()
    parser.add_argument("--config",
                        default="~/.config/tr2ynab/tr2ynab.cfg",
                        help="Path to the config file")
    parser.add_argument("--version",
                        action="version",
                        version=f"%(prog)s v{__version__}")

    args = parser.parse_args()

    logger = logging.getLogger()
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.info("Reading config file from %s", os.path.expanduser(args.config))
    Settings.load(os.path.expanduser(args.config))
    logger.setLevel(Settings.get().config.get('main', 'log_level', fallback='INFO'))

    transactions = tr_load_transactions()

    ynab_push_transactions(transactions)


if __name__ == "__main__":
    main()
