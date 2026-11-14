import hashlib
import struct
from types import SimpleNamespace
import pytest
from dw2studio.pak import PakFile, MAGIC
from dw2studio.port_mod import plan, export


def make_pak(tmp_path, payload=b'hello world', lba=123):
    h = bytearray(80)
    struct.pack_into('<8s6I', h, 0, MAGIC, 1, 80, 1, 80, 64, 0)
    entry = struct.pack('<4I2Q', 42, lba, 1, 0, 144, len(payload)) + hashlib.sha256(payload).digest()
    path = tmp_path / 'test.pak'
    path.write_bytes(h + entry + payload)
    return PakFile(path)


def session_for(payload=b'hello world', replacement=b'HELLO WORLD'):
    edit = SimpleNamespace(path='TEST.BIN', lba=123, original=payload,
                           replacement=replacement, relocate=False, label='test')
    return SimpleNamespace(edits={('TEST.BIN', 123): edit}, _check_source=lambda: None)


def test_pak_read_extract_and_hash(tmp_path):
    pak = make_pak(tmp_path)
    assert pak.read(42) == b'hello world'
    destination = tmp_path / 'out.bin'
    pak.extract(42, destination)
    assert destination.read_bytes() == b'hello world'
    with pytest.raises(FileExistsError):
        pak.extract(42, destination)


def test_overlay_export_and_no_overwrite(tmp_path):
    pak = make_pak(tmp_path)
    session = session_for()
    assert plan(session, pak)[0]['id'] == 42
    result = export(session, pak, tmp_path / 'port')
    assert result['count'] == 1
    assert (tmp_path / 'port/Mods/files/002A.bin').read_bytes() == b'HELLO WORLD'
    assert pak.read(42) == b'hello world'
    with pytest.raises(FileExistsError):
        export(session, pak, tmp_path / 'port')


def test_overlay_rejects_mismatch(tmp_path):
    pak = make_pak(tmp_path)
    with pytest.raises(ValueError, match='no unique'):
        plan(session_for(payload=b'wrong bytes'), pak)
    with pytest.raises(ValueError, match='exactly'):
        plan(session_for(replacement=b'too short'), pak)
