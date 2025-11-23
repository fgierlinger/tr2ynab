def test_convert_value_string_to_milliunits():
    from tr2ynab.tr2ynab import convert_value_string_to_milliunits

    assert convert_value_string_to_milliunits("1,234.56") == 1234560
    assert convert_value_string_to_milliunits("1,234") == 1234000
    assert convert_value_string_to_milliunits("0.99") == 990
    assert convert_value_string_to_milliunits("100") == 100000
    assert convert_value_string_to_milliunits("12,345,678.901") == 12345678901
