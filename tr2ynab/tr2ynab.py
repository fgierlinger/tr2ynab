"""
This module provides functionality to fetch transactions from Trade Republic and
push them to YNAB (You Need A Budget). It includes classes and functions to
handle transactions, manage configuration, and interact with the YNAB API.

Classes:
    - PyTRExit: Custom exception to handle pytr.dl exit behavior.
    - Transaction: Represents a financial transaction with attributes such as
      date, type, value, and more.
    - YNABSettings: Stores YNAB configuration details like budget ID, access
      token, and account ID.

Functions:
    - get_last_import_timestamp: Retrieves the last import timestamp from the
      configuration file.
    - save_last_import_timestamp: Saves the last import timestamp to the
      configuration file.
    - tr_load_transactions: Fetches transactions from Trade Republic since the
      last import timestamp.
    - ynab_push_transactions: Pushes transactions to YNAB using the provided
      YNAB settings.

Constants:
    - CONFIG_DIR: Path to the configuration directory.
    - LAST_IMPORT_FILE: Path to the file storing the last import timestamp.
"""
import asyncio
from dataclasses import dataclass
import datetime
import json
import builtins
from pathlib import Path
import shutil
import tempfile
from typing import List
from pytr.dl import Timeline, TransactionExporter, Event
from pytr.account import login
import ynab
import configparser


class PyTRExit(Exception):
    """Custom exception to exit pytr.dl."""


def fake__exit(code=None):
    """Fake exit function to prevent pytr.dl from exiting."""
    raise PyTRExit(code)


__original_exit = builtins.exit
builtins.exit = fake__exit


@dataclass
class Transaction:  # pylint: disable=too-many-instance-attributes
    """Transaction class."""
    Date: datetime.datetime  # pylint: disable=invalid-name
    Type: str  # pylint: disable=invalid-name
    Value: float  # pylint: disable=invalid-name
    Note: str  # pylint: disable=invalid-name
    ISIN: str | None  # pylint: disable=invalid-name
    Shares: str | None  # pylint: disable=invalid-name
    Fees: str | None  # pylint: disable=invalid-name
    Taxes: str | None  # pylint: disable=invalid-name

    def __post_init__(self):
        if isinstance(self.Date, str):
            self.Date = datetime.datetime.fromisoformat(self.Date)
        self.Note = self.Note.replace("Card Payment - ", "")


class Settings:
    """Class to hold YNAB settings."""
    _instance = None
    config: configparser.ConfigParser
    config_path: Path

    def __init__(self, config_path: str) -> None:
        if Settings._instance is not None:
            raise RuntimeError("Use Settings.get() instead of calling Settings() directly")

        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        parser = configparser.ConfigParser()
        parser.read(config_path)

        self.config = parser
        self.config_path = path

    @classmethod
    def load(cls, config_path: str) -> 'Settings':
        """Load settings from the config file."""
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance

    @classmethod
    def get(cls) -> 'Settings':
        """Get the singleton instance of Settings."""
        if cls._instance is None:
            raise RuntimeError("Settings not loaded. Call Settings.load(config_path) first.")
        return cls._instance


def get_last_import_timestamp() -> datetime.datetime:
    """Retrieve the last import timestamp from the config file."""
    last_import_file = Path(Settings.get().config.get('main', 'last_import_file'))

    if not last_import_file.exists():
        # Default to 7 days ago if no timestamp is found
        return datetime.datetime.now() - datetime.timedelta(days=7)
    with open(last_import_file, "r", encoding="utf-8") as f:
        timestamp = f.read().strip()
        return datetime.datetime.fromisoformat(timestamp)


def save_last_import_timestamp(timestamp: datetime.datetime) -> None:
    """Save the last import timestamp to the config file."""
    last_import_file = Path(Settings.get().config.get('main', 'last_import_file'))
    last_import_file.parent.mkdir(parents=True, exist_ok=True)
    with open(last_import_file, "w", encoding="utf-8") as f:
        f.write(timestamp.isoformat())


def tr_load_transactions(lang: str = "en") -> List[Transaction]:
    """Load transactions from Trade Republic."""
    last_import_timestamp = get_last_import_timestamp()
    print(f"Fetching transactions since: {last_import_timestamp}")

    tempdir = Path(tempfile.mkdtemp())
    tl = Timeline(
        login(
            phone_no=Settings.get().config.get('TradeRepublic', 'phone_no'),
            pin=Settings.get().config.get('TradeRepublic', 'pin'),
            store_credentials=True
        ),
        output_path=tempdir,
        not_before=last_import_timestamp.timestamp()
    )
    asyncio.run(tl.tl_loop())
    events = tl.events

    account_transactions_file = tempdir / ("account_transactions." + "json")
    with open(account_transactions_file, "w", encoding="utf-8") as f:
        TransactionExporter(
            lang=lang,
            date_with_time=True,
            decimal_localization=True
        ).export(
            f,
            [Event.from_dict(item) for item in events],
            sort=False,
            format="json"
        )

    # file has csv ending but is json
    with open(account_transactions_file, "r", encoding='utf-8') as f:
        data = [Transaction(**(json.loads(line))) for line in f.readlines()]

    # Save the current timestamp as the last import timestamp
    save_last_import_timestamp(datetime.datetime.now())

    # Cleanup tempdir
    if tempdir != ".":
        print(f"Cleaning up tempdir: {tempdir}")
        shutil.rmtree(tempdir)

    return data


def convert_value_string_to_milliunits(value: str) -> int:
    """Convert a value string to milliunits for YNAB.

    Args:
        value (str): value string with optional commas and decimal point.

    Returns:
        int: value in milliunits.
    """
    # YNAB expects amounts in milliunits (e.g., $1.00 = 1000). Trade
    # Republic retuns value strings with commas as thousands separators and
    # dots as decimal separators. If the comma value is 00, the dot is omitted.
    value_cleaned = value.replace(',', '')
    if '.' in value_cleaned:
        whole, fraction = value_cleaned.split('.')
        fraction = (fraction + '000')[:3]  # Ensure three decimal places
    else:
        whole = value_cleaned
        fraction = '000'

    if whole.startswith('-'):
        return int(whole) * 1000 - int(fraction)
    return int(whole) * 1000 + int(fraction)


def ynab_push_transactions(transactions: List[Transaction]) -> None:
    """Push transactions to YNAB."""
    configuration = ynab.Configuration(
        access_token=Settings.get().config.get('YNAB', 'access_token')
    )
    ynab_transactions = []
    for transaction in transactions:
        ynab_transactions.append(ynab.NewTransaction(
            budget_id=Settings.get().config.get('YNAB', 'budget_id'),
            account_id=Settings.get().config.get('YNAB', 'account_id'),
            date=transaction.Date.strftime("%Y-%m-%d"),
            amount=convert_value_string_to_milliunits(transaction.Value),
            payee_name=transaction.Note,
            cleared="cleared",
            approved=False
        ))

    with ynab.ApiClient(configuration) as api_client:
        transaction_api = ynab.TransactionsApi(api_client)
        ptw = ynab.PostTransactionsWrapper(transactions=ynab_transactions)
        out = transaction_api.create_transaction(
            Settings.get().config.get('YNAB', 'budget_id'),
            ptw
        )
        print(f"Created {len(out.data.transaction_ids)} transactions in YNAB")
