"""DIGIMNDT evolution rules, following Digi_GetEvolutionTarget in gamedata.c.

18-byte record: rank at +4 high nibble, five DP bounds at +8, four u8
targets at +13. There is no per-species level threshold in these bytes.
"""
from .battle_skills import BaseTable, discover_tables


def target_for(bounds, targets, dp):
    if type(dp) is not int or not 0 <= dp <= 255:
        raise ValueError('DP muss zwischen 0 und 255 liegen.')
    if not targets[0]:
        return 0
    for i in range(4):
        if bounds[i + 1] == 0 or bounds[i] <= dp < bounds[i + 1]:
            return targets[i]
    raise ValueError('DP-Tabelle hat keinen sicheren Abschluss.')


class EvolutionRepository:
    def __init__(self, session, entries):
        self.session = session
        self.entry = discover_tables(session, entries, filenames=('DIGIMNDT.BIN',))['DIGIMNDT.BIN']

    def info(self, identifier):
        data = self.session.current(self.entry)
        table = BaseTable(data)
        if identifier not in table.records:
            raise ValueError('Digimon besitzt keinen DIGIMNDT-Eintrag.')
        offset = table.records[identifier][0]
        bounds, targets = list(data[offset+8:offset+13]), list(data[offset+13:offset+17])
        rows = []
        if targets[0]:
            for i, target in enumerate(targets):
                rows.append({'min_dp': bounds[i], 'target': target})
                if bounds[i+1] == 0:
                    break
            else:
                raise ValueError('Digitationstabelle ohne Abschluss; Bearbeitung wird verweigert.')
        return {'rank': data[offset+4] >> 4, 'dna_group': data[offset+3], 'rows': rows,
                'bounds': bounds, 'targets': targets,
                'choices': sorted(i for i in table.records if 1 <= i <= 255)}

    def change(self, identifier, rows, rank=None, dna_group=None):
        before = self.session.current(self.entry)
        table = BaseTable(before)
        self.info(identifier)
        if not isinstance(rows, list) or len(rows) > 4:
            raise ValueError('Höchstens vier Digitationsziele möglich.')
        bounds, targets = [0]*5, [0]*4
        last = -1
        for i, row in enumerate(rows):
            dp, target = row['min_dp'], row['target']
            if type(dp) is not int or not 0 <= dp <= 255 or dp <= last or (i == 0 and dp != 0):
                raise ValueError('DP-Grenzen müssen bei 0 beginnen und streng steigen (0–255).')
            if type(target) is not int or not 1 <= target <= 255 or target not in table.records or target == identifier:
                raise ValueError('Digitationsziel muss eine andere vorhandene 8-Bit-Digimon-ID sein.')
            bounds[i], targets[i], last = dp, target, dp
        offset = table.records[identifier][0]
        out = bytearray(before)
        out[offset+8:offset+13], out[offset+13:offset+17] = bytes(bounds), bytes(targets)
        if rank is not None:
            if type(rank) is not int or not 0 <= rank <= 3:
                raise ValueError('Stufe muss 0 (Rookie) bis 3 (Mega) sein.')
            out[offset+4] = (out[offset+4] & 15) | (rank << 4)
        if dna_group is not None:
            if type(dna_group) is not int or not 0 <= dna_group <= 255:
                raise ValueError('DNA-Gruppe muss 0–255 sein.')
            out[offset+3] = dna_group
        if out == before:
            return False
        for dp in range(256):
            target_for(bounds, targets, dp)
        self.session.stage(self.entry, out, f'Digitation / DP #{identifier:03}')
        return True
