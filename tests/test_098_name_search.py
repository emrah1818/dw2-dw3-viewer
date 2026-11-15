"""Regression tests for DW3 model name search without proprietary game files."""
from dw2studio.dw3_names import matches, rank


ROW = {
    "id": 150,
    "file_number": 359,
    "fighter_ids": [42],
    "name": "Imperialdramon-F",
    "code": "IPDF",
    "file": "M359IPDF.BIN",
    "raw_name": "",
    "aliases": ["Imperialdramon Fighter Mode", "Imperialdramon FM"],
}


def test_find_by_name_alias_and_code():
    for query in ("Imperialdramon Fighter Mode", "fighter mode", "IPDF", "m359ipdf", "imperialdramon-f"):
        assert matches(ROW, query)
    assert not matches(ROW, "WarGreymon")


def test_find_by_catalog_file_and_fighter_id():
    for query in ("150", "#150", "359", "#359", "42"):
        assert matches(ROW, query)
    assert not matches(ROW, "999")


def test_exact_name_ranked_first():
    assert rank(ROW, "Imperialdramon Fighter Mode") == 0
