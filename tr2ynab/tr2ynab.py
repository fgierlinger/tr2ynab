import asyncio
from dataclasses import dataclass
import datetime
import json
import builtins
import shutil
import tempfile
import os
from typing import List
from pytr.dl import DL
from pytr.account import login
import ynab


CONFIG_DIR = os.path.expanduser("~/.config/tr2ynab")
LAST_IMPORT_FILE = os.path.join(CONFIG_DIR, "last_import_timestamp.txt")


class PyTRExit(Exception):
    """Custom exception to exit pytr.dl."""
    pass


def fake__exit(code=None):
    """Fake exit function to prevent pytr.dl from exiting."""
    raise PyTRExit(code)


__original_exit = builtins.exit
builtins.exit = fake__exit


@dataclass
class Transaction:
    """Transaction class."""
    Date: datetime.datetime
    Type: str
    Value: float
    Note: str
    ISIN: str | None
    Shares: str | None
    Fees: str | None
    Taxes: str | None

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


def tr_load_transactions(phone_no: str, pin: str) -> List[Transaction]:
    """Load transactions from Trade Republic."""
    last_import_timestamp = get_last_import_timestamp()
    print(f"Fetching transactions since: {last_import_timestamp}")

    tempdir = tempfile.mkdtemp()
    dl = DL(
        login(
            phone_no=phone_no,
            pin=pin,
            store_credentials=True
        ),
        output_path=tempdir,
        filename_fmt="{iso_date} {time} {title}",
        since_timestamp=last_import_timestamp.timestamp(),
        max_workers=8,
        universal_filepath=False,
        lang="en",
        date_with_time=True,
        decimal_localization=False,
        sort_export=False,
        format_export="json"
    )
    try:
        asyncio.run(dl.dl_loop())
    except PyTRExit as e:
        if e.args[0] != 0:
            raise e
    except Exception as e:
        print(f"Error in dl.dl_loop(): {e}")

    with open(f"{tempdir}/account_transactions.csv", "r", encoding='utf-8') as f:  # file has csv ending but is json
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
            amount=int(transaction.Value * 1000),  # YNAB expects milliunits
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
