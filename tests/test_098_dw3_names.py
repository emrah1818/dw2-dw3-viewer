"""0.98: DW3-Namen aus DIGNAM (synthetische Daten, keine Spieldaten)."""
import struct
from dw2studio import dw3_names as N


def enc(text):
    """Text in DW3's own glyph bytes (inverse of decode for the characters used here)."""
    out = bytearray()
    for ch in text:
        if ch == ' ':
            out += bytes([1, 1])                      # Symbol 1: Leerzeichen (0x8140)
        elif ch == '-':
            out += bytes([1, 26])                     # Symbol 26: Minus (0x817C)
        else:
            code = int.from_bytes(ch.encode('shift_jis') if not ch.isascii() else
                                  __import__('unicodedata').normalize('NFKC', ch).translate(
                                      {i: i + 0xFEE0 for i in range(0x21, 0x7F)}).encode('shift_jis'), 'big')
            out.append(N.GLYPHS.index(code) + 4)
    return bytes(out) + b'\0'


def table(strings):
    body = b''.join(enc(s) for s in strings)
    head = 4 + 4 * len(strings)
    offs, at = [], head
    for s in strings:
        offs.append(at); at += len(enc(s))
    return struct.pack('<i', len(strings) - 1) + struct.pack(f'<{len(strings)}i', *offs) + body


def test_decode_letters_digits_icons():
    assert N.decode(enc('WarGreymon')) == 'WarGreymon'
    assert N.decode(enc('Imperialdramon-F')) == 'Imperialdramon-F'
    assert N.decode(enc('BK WarGreymon')) == 'BK WarGreymon'
    assert N.decode(enc('Numemon2')) == 'Numemon2'


def test_read_dignam_index_is_fighter_kind():
    names = N.read_dignam(table(['', 'Kotemon', 'Kumamon', 'Meramon']))
    assert names[0] == '' and names[1] == 'Kotemon' and names[3] == 'Meramon'


def test_search_name_part_alias_code_and_ids():
    row = {'name': 'Imperialdramon-F', 'code': 'IPDF', 'file': 'M359IPDF.BIN', 'aliases': N.ALIASES['Imperialdramon-F'],
           'id': 143, 'file_number': 834, 'name_index': 44, 'fighter_ids': [359]}
    for q in ('imperialdramon', 'IMPERIALDRAMON-F', 'Fighter Mode', 'imperialdramon fm', 'ipdf', 'm359', '359', '#359', 'dramon f'):
        assert N.matches(row, q), q
    for q in ('paladin', 'WarGreymon', '360', '834', '44'):
        assert not N.matches(row, q), q
    assert N.matches(row, '')


def test_rank_exact_before_partial():
    a = {'name': 'WarGreymon', 'aliases': []}; b = {'name': 'BK WarGreymon', 'aliases': N.ALIASES['BK WarGreymon']}
    assert N.rank(a, 'wargreymon') == 0 and N.rank(b, 'wargreymon') == 2 and N.rank(b, 'blackwar') == 1
