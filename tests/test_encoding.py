import pytest

from articlenizer import encode_string

def test_replacement():
    s = 'Sómè ünicôdè shóûld bè rèplâcéd.'
    s, _ = encode_string.handle_unicode_characters(s)
    assert s == 'Some unicode should be replaced.'

def test_removal():
    s = '❨Some⁆ unicode ௵should be꜐ removed⑩.'
    s, _ = encode_string.handle_unicode_characters(s)
    assert s == 'Some unicode should be removed.'

def test_trademarks():
    s = 'The following should all be the same: ©™®'
    s, _ = encode_string.handle_unicode_characters(s)
    assert s == 'The following should all be the same: ™™™'

def test_quotations():
    s = '«“Different quotes should be the same.»”'
    s, _ = encode_string.handle_unicode_characters(s)
    assert s == '““Different quotes should be the same.””'