# pylint: disable=missing-function-docstring,missing-module-docstring
import os
from tempfile import mkstemp

from pytest import raises
from tr2ynab.tr2ynab import convert_value_string_to_milliunits, Settings


def test_config_early_load():
    assert raises(RuntimeError, Settings.get)


def test_convert_value_string_to_milliunits():

    assert convert_value_string_to_milliunits("1,234.56") == 1234560
    assert convert_value_string_to_milliunits("1,234") == 1234000
    assert convert_value_string_to_milliunits("0.99") == 990
    assert convert_value_string_to_milliunits("100") == 100000
    assert convert_value_string_to_milliunits("12,345,678.901") == 12345678901
    assert convert_value_string_to_milliunits("-40.28") == -40280
    assert convert_value_string_to_milliunits("0") == 0
    assert convert_value_string_to_milliunits("-0.01") == -10
    assert convert_value_string_to_milliunits("-1,234.5") == -1234500


def test_config_load():
    tempfile = mkstemp()[1]
    with open(tempfile, "w", encoding='utf-8') as f:
        f.write("""
# -*- coding: utf-8 -*-
[main]
last_import_file = ./last_import_timestamp.txt

[TradeRepublic]
phone_no = +491234567890
pin = 1234

[YNAB]

""")
    Settings.load(tempfile)
    assert Settings.get().config['main']['last_import_file'] == "./last_import_timestamp.txt"
    assert Settings.get().config.get('TradeRepublic', 'phone_no') == "+491234567890"
    assert Settings.get().config.get('TradeRepublic', 'pin') == "1234"
    os.remove(tempfile)
