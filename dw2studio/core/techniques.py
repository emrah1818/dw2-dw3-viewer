"""Individual techniques: a copy of an existing technique under a free id, used by one Digimon.

The copy keeps the source's effects, animation parts, sound and flags (all inside its WAZADATA
record, see SkillTable.cloned). Name, description, MP, power, element (specialty), start
animation (F/G/H, cast bits) and the other documented fields are then the copy's own. It is
assigned as the Digimon's learnable technique (DIGIMNDT +2) and/or to its enemy slots in
ENEMYSET. No other Digimon refers to the new id, so nothing else changes.
"""
from .battle_skills import AttackRepository, BaseTable, EnemyTable, SkillTable


class TechniqueRepository:
    def __init__(self, session, entries):
        self.session = session
        self.attacks = AttackRepository(session, entries)
        self.files = self.attacks.entries

    def tables(self):
        return self.attacks.tables()

    def usage(self, technique):
        skills, base, enemies = self.tables()
        default = [i for i, (off, skill) in base.records.items() if skill == technique]
        found = [(k, r.identifier) for k, r in enemies.records.items() if technique in r.skills]
        users = set(default) | {d for _, d in found}
        return {'technique': technique, 'default_of': default, 'encounters': [list(k) for k, _ in found],
                'digimon': sorted(users), 'shared': len(users) > 1}

    def catalog(self):
        skills, base, enemies = self.tables()
        users = {}
        for i, (off, skill) in base.records.items():
            users.setdefault(skill, set()).add(i)
        for k, r in enemies.records.items():
            for s in r.skills:
                users.setdefault(s, set()).add(r.identifier)
        return [{'id': i, 'name': r.name, 'mp': r.mp, 'power': r.power, 'specialty': r.specialty,
                 'cast': r.cast, 'category': r.category, 'target': r.target, 'rank': r.rank,
                 'users': sorted(users.get(i, ()))} for i, r in sorted(skills.records.items())]

    def create(self, digimon, source, name, *, description=None, values=None, as_default=True, encounters=(), new_id=None):
        skills, base, enemies = self.tables()
        if as_default and digimon not in base.records:
            raise ValueError('Dieses Digimon hat keinen DIGIMNDT-Eintrag für eine erlernbare Technik.')
        encounters = [tuple(k) for k in encounters]
        for key in encounters:
            if key not in enemies.records or enemies.records[key].identifier != digimon:
                raise ValueError('Gegnerplatz gehört nicht zu diesem Digimon.')
        if not as_default and not encounters:
            raise ValueError('Die neue Technik muss mindestens einem Platz zugewiesen werden.')
        new_id = new_id or (skills.free_ids() or [None])[0]
        if new_id is None:
            raise ValueError('Keine freie Technik-ID 1–255 mehr.')
        wazadata = skills.cloned(source, new_id, name, description, values)
        files = {'WAZADATA.BIN': wazadata}
        if as_default:
            files['DIGIMNDT.BIN'] = base.changed(digimon, new_id)
        if encounters:
            changes = {}
            for key in encounters:
                old = enemies.records[key]
                slots = list(old.skills)
                # replace the slot that held SOURCE, else the first empty slot, else slot 1
                pick = slots.index(source) if source in slots else (slots.index(0) if 0 in slots else 0)
                slots[pick] = new_id
                changes[key] = (slots, list(old.rules))
            files['ENEMYSET.BIN'] = enemies.changed(changes, SkillTable(wazadata).records)
        for name_, data in files.items():
            self.session.stage(self.files[name_], data, f'Eigene Technik {new_id} für #{digimon:03}')
        return {'id': new_id, 'files': sorted(files)}

    def edit(self, technique, values=None, name=None, *, digimon):
        """Change an individual technique (one created here). Shared techniques: values only via
        the existing global attack editor, so other Digimon are never changed by accident."""
        info = self.usage(technique)
        if info['shared'] or set(info['digimon']) - {digimon}:
            raise ValueError('Diese Technik nutzen mehrere Digimon. Für Änderungen nur an einem Digimon '
                             'zuerst eine eigene Technik anlegen.')
        skills, _, _ = self.tables()
        if technique not in skills.records:
            raise ValueError('Technik fehlt.')
        data = skills.data
        if name is not None and name != skills.records[technique].name:
            data = _renamed(SkillTable(data), technique, name)
        if values:
            data = SkillTable(data).changed({technique: values})
        if data == skills.data:
            return False
        self.session.stage(self.files['WAZADATA.BIN'], data, f'Technik {technique} bearbeitet')
        return True


def _renamed(table, technique, name):
    """New name text behind the end row; only the record's name offset changes."""
    import struct
    from .battle_skills import _encode_text
    encoded = _encode_text(name, 17, 'Technikname')
    end = table._find_end(table.data, table.records_start)
    out = bytearray(table.data)
    if len(out) < end + 68:
        out += bytes(end + 68 - len(out))
    out = bytearray(bytes(out).rstrip(b'\0')) if len(out) > end + 68 else out
    if len(out) < end + 68:
        out += bytes(end + 68 - len(out))
    at = len(out)
    out += encoded + b'\xff'
    out += bytes(-len(out) % 4)
    if len(out) < len(table.data):
        out += bytes(len(table.data) - len(out))
    struct.pack_into('<I', out, table.records[technique].offset + 0x24, at)
    SkillTable(bytes(out))
    return bytes(out)
