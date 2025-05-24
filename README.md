# TR2YNAB

A command-line tool to synchronize Trade Republic transactions with You Need A Budget (YNAB).

## Description

TR2YNAB is a Python-based utility that automatically fetches your transaction history from Trade Republic and imports it into your YNAB budget. It keeps track of the last import date to avoid duplicate transactions and handles various transaction types including card payments, trades, and fees.

### Features

- Automatic authentication with Trade Republic
- Smart transaction synchronization using last import date
- Configurable import settings
- Support for all Trade Republic transaction types
- Automatic conversion to YNAB transaction format
- Command-line interface for easy automation

## Installation

Install TR2YNAB using pip:

```bash
pip install tr2ynab
```

## Usage

1. Create a configuration file at `~/.config/tr2ynab/tr2ynab.cfg` with your credentials:

```ini
[TradeRepublic]
phone_no = "+491234567890"
pin = "123456"

[YNAB]
access_token = "your_ynab_access_token"
budget_id = "your_ynab_budget_id"
account_id = "your_ynab_account_id"
```

2. Run the synchronization:

```bash
tr2ynab --config ~/.config/tr2ynab/tr2ynab.cfg
```

### Command Line Options

- `--config`: Path to the configuration file (default: `~/.config/tr2ynab/tr2ynab.cfg`)
- `--version`: Show program version and exit

## Configuration

### Trade Republic Section

- `phone_no`: Your Trade Republic phone number (with country code)
- `pin`: Your Trade Republic PIN

### YNAB Section

- `access_token`: Your YNAB API access token
- `budget_id`: The ID of your YNAB budget
- `account_id`: The ID of your YNAB account where transactions should be imported

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/tr2ynab.git
cd tr2ynab

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Author

Frédéric Gierlinger <frederic.gierlinger@gmail.com>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
