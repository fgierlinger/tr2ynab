## v1.1.0 (2025-12-03)

### Feat

- move last import timestamp saving to ynab_push_transactions
- enhance logging by using logging module
- refactor ynab methods to use Settings for YNAB credentials
- refactor transaction loading to use Settings for TradeRepublic credentials
- implement Settings class for configuration management and update tests

### Fix

- add check for empty transactions in ynab_push_transactions #7

## v1.0.4 (2025-12-03)

### Fix

- update pytr dependency to version 0.4.4

## v1.0.3 (2025-11-23)

### Fix

- enhance convert_value_string_to_milliunits for negative values and add tests

## v1.0.2 (2025-11-23)

### Fix

- add convert_value_string_to_milliunits function and corresponding tests #4

## v1.0.1 (2025-11-16)

### Fix

- use export_transaction logic from pytr to fix KeyError

## v1.0.0 (2025-05-25)

### Feat

- add LICENSE and README files with project details and usage instructions

## v0.4.0 (2025-05-24)

### Feat

- add versioning support and update main script for version display

## v0.3.0 (2025-05-24)

### Feat

- add initial implementation of the main script and project configuration

## v0.2.0 (2025-05-24)

### Feat

- initial commit
