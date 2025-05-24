# pylint: disable=missing-module-docstring,missing-function-docstring
from argparse import ArgumentParser
from configparser import ConfigParser
import os
from tr2ynab import ynab_push_transactions, tr_load_transactions
from tr2ynab.tr2ynab import YNABSettings
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

    config = ConfigParser()
    print(f"Reading config file from {os.path.expanduser(args.config)}")
    config.read(os.path.expanduser(args.config))

    ynab_settings = YNABSettings(
        budget_id=config.get("YNAB", "budget_id"),
        access_token=config.get("YNAB", "access_token"),
        account_id=config.get("YNAB", "account_id"),
    )

    transactions = tr_load_transactions(
        phone_no=config.get("TradeRepublic", "phone_no"),
        pin=config.get("TradeRepublic", "pin"),
    )

    ynab_push_transactions(transactions, ynab_settings)


if __name__ == "__main__":
    main()
