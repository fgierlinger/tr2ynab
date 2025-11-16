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
import os
from typing import List
from pytr.dl import Timeline, TransactionExporter, Event
from pytr.account import login
import ynab


CONFIG_DIR = os.path.expanduser("~/.config/tr2ynab")
LAST_IMPORT_FILE = os.path.join(CONFIG_DIR, "last_import_timestamp.txt")


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


@dataclass
class YNABSettings:
    """YNAB settings."""
    budget_id: str
    access_token: str
    account_id: str


def get_last_import_timestamp() -> datetime.datetime:
    """Retrieve the last import timestamp from the config file."""
    if not os.path.exists(LAST_IMPORT_FILE):
        # Default to 7 days ago if no timestamp is found
        return datetime.datetime.now() - datetime.timedelta(days=7)
    with open(LAST_IMPORT_FILE, "r", encoding="utf-8") as f:
        timestamp = f.read().strip()
        return datetime.datetime.fromisoformat(timestamp)


def save_last_import_timestamp(timestamp: datetime.datetime) -> None:
    """Save the last import timestamp to the config file."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    with open(LAST_IMPORT_FILE, "w", encoding="utf-8") as f:
        f.write(timestamp.isoformat())


def tr_load_transactions(phone_no: str, pin: str, lang: str = "en") -> List[Transaction]:
    """Load transactions from Trade Republic."""
    last_import_timestamp = get_last_import_timestamp()
    print(f"Fetching transactions since: {last_import_timestamp}")

    tempdir = Path(tempfile.mkdtemp())
    tl = Timeline(
        login(
            phone_no=phone_no,
            pin=pin,
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


def ynab_push_transactions(transactions: List[Transaction], ynab_settings: YNABSettings) -> None:
    """Push transactions to YNAB."""
    configuration = ynab.Configuration(
        access_token=ynab_settings.access_token
    )

    ynab_transactions = []
    for transaction in transactions:
        ynab_transactions.append(ynab.NewTransaction(
            budget_id=ynab_settings.budget_id,
            account_id=ynab_settings.account_id,
            date=transaction.Date.strftime("%Y-%m-%d"),
            amount=int(float(transaction.Value) * 1000),  # YNAB expects milliunits
            payee_name=transaction.Note,
            cleared="cleared",
            approved=False
        ))

    with ynab.ApiClient(configuration) as api_client:
        transaction_api = ynab.TransactionsApi(api_client)
        ptw = ynab.PostTransactionsWrapper(transactions=ynab_transactions)
        out = transaction_api.create_transaction(
            ynab_settings.budget_id,
            ptw
        )
        print(f"Created {len(out.data.transaction_ids)} transactions in YNAB")
