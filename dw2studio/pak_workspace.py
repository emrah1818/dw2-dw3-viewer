"""Read-only PAK mount using the existing DW2 editors and native converter.

Names come from the bundled USA file-ID map; table parsers validate the bytes.
No ISO is fabricated and the original PAK is never rewritten.
"""
import bisect
import hashlib
import json
import os
from pathlib import Path
from .pak import PakFile
from .core.disc import Entry
from .core.edit_session import EditSession, FileEdit


class PakDisc:
    def __init__(self, path):
        self.source = self.path = Path(path).resolve()
        self.pak = PakFile(self.path)
        self.sector_size = 2048
        self.sector_count = max(e.lba + e.sectors for e in self.pak.entries)
        self.volume = 'DW2 PAK'
        root = Path(os.environ.get('DW2_DATA_DIR') or Path(__file__).resolve().parent.parent / 'data')
        names = json.loads((root / 'native_file_ids_us.json').read_text(encoding='utf-8'))
        from .core.digimon_names import FILE_INDEX as name_ids
        from .core.battle_skills import FILE_INDEX as battle_ids
        names.update(name_ids)
        names.update(battle_ids)
        by_id = {}
        for name, identifier in names.items():
            if identifier in by_id and by_id[identifier] != name:
                raise ValueError('Ambiguous bundled PAK file names')
            by_id[identifier] = name
        self.entries = [Entry('PAK/' + by_id.get(e.id, f'INDEX_{e.id:04X}.BIN'), e.lba, e.size, False)
                        for e in self.pak.entries if e.format == 0]
        self.allocations = sorted((e for e in self.pak.entries if e.format == 0), key=lambda e: e.lba)
        self.starts = [e.lba for e in self.allocations]

    def close(self):
        pass

    def read(self, lba, size):
        i = bisect.bisect_right(self.starts, lba) - 1
        if i < 0:
            raise ValueError('LBA is not part of a PAK data allocation')
        e = self.allocations[i]
        offset = (lba - e.lba) * 2048
        if size < 0 or offset + size > e.size:
            raise ValueError('Read exceeds PAK allocation')
        return self.pak.read(e.id)[offset:offset + size]

    def extract(self, entry, destination):
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as out:
            out.write(self.read(entry.lba, entry.size))


class PakSession(EditSession):
    def __init__(self, path):
        self.disc = PakDisc(path)
        self.pak = self.disc.pak
        self.source = self.disc.path
        self.sector_size = 2048
        self.stamp = self._stamp()
        self.edits = {}

    def original(self, entry):
        self._check_source()
        if entry.directory:
            raise ValueError('Cannot read a directory')
        return self.disc.read(entry.lba, entry.size)

    def stage(self, entry, data, label='Datei ersetzt', *, relocate=False):
        data = bytes(data)
        if relocate or len(data) != entry.size:
            raise ValueError('Der PC-Port unterstützt hier nur Ersatz in Originalgröße. Größere Dateien benötigen eine Engine-Erweiterung.')
        original = self.original(entry)
        key = (entry.path, entry.lba)
        for other_key, edit in self.edits.items():
            if key != other_key and max(entry.lba * 2048, edit.lba * 2048) < min(entry.lba * 2048 + entry.size, edit.lba * 2048 + len(edit.original)):
                raise ValueError('Überlappende PAK-Dateien können nicht getrennt ersetzt werden.')
        if data == original:
            self.edits.pop(key, None)
        else:
            self.edits[key] = FileEdit(entry.path, entry.lba, original, data, label)
        return self.edits.get(key)

    def save(self, destination, *, overwrite=False):
        raise ValueError('PAK bleibt unverändert. Bitte „PC-Port-Mod exportieren“ verwenden.')


def open_workspace(path):
    from .core.catalog import build_catalog
    from .core.digimon_names import NameRepository
    session = PakSession(path)
    entries = session.disc.entries
    catalog = build_catalog(entries)
    names = NameRepository(session, entries).names()
    for c in catalog:
        if c.id in names:
            c.name, c.verified_name = names[c.id], True
    stamp = f'{session.source}:{session.stamp}'
    return session, entries, catalog, hashlib.sha256(stamp.encode()).hexdigest()
