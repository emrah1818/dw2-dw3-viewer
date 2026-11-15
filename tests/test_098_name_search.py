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


def test_shared_names_with_missing_name_indices(monkeypatch):
    """Multiple variants must not crash when a fighter has no name index."""
    from types import SimpleNamespace
    from dw2studio import dw3_names
    from dw2studio import dw3_fighters

    class Disc:
        def read(self, lba, size):
            return b""

    monkeypatch.setattr(dw3_fighters, "_exe", lambda disc: ("SLUS_014.36", None))
    monkeypatch.setattr(dw3_fighters, "fighters", lambda disc: (
        {100: (10, 1), 101: (11, 1)},
        [
            {"model": (100, 0), "kind": 7, "id": 7, "enemy": False},
            {"model": (101, 0), "kind": 7, "id": 8, "enemy": True},
        ],
    ))
    monkeypatch.setattr(dw3_names, "read_dignam", lambda data: {7: "Greymon"})
    # Simulate the USA name file and two model files.
    entries = [
        SimpleNamespace(path="M100GREY.BIN", lba=10),
        SimpleNamespace(path="M101GREY.BIN", lba=11),
    ]
    # No DIGNAM file means names are unreadable; fallback must remain safe.
    result = dw3_names.build(Disc(), entries)
    assert len(result["models"]) == 2
    assert all(row["status"] == "unreadable" for row in result["models"])
