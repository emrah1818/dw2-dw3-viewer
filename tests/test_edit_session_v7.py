import json
import struct
from pathlib import Path
import pytest
from dw2studio.core.disc import Entry
from dw2studio.core.edit_session import EditSession
from dw2studio.core.psx_patch import regenerate_form1,validate_form1_ecc
from dw2studio.core.psx_sector import SYNC


def sector(payload):
    raw=bytearray(2352);raw[:12]=SYNC;raw[15]=2;raw[16:20]=bytes([1,0,8,0]);raw[20:24]=raw[16:20];raw[24:2072]=payload
    return regenerate_form1(raw)

@pytest.mark.parametrize('size',[2048,2352])
def test_multi_file_composition_one_export_and_padding(tmp_path,size):
    payloads=[bytes([i])*2048 for i in range(8)]
    source=tmp_path/'game.bin';source.write_bytes(b''.join(payloads if size==2048 else map(sector,payloads)))
    before=source.read_bytes();session=EditSession(source,size)
    a=Entry('M003TEST.BIN',1,2200,False);b=Entry('M004TEST.BIN',4,100,False)
    data=bytearray(session.current(a));data[0]=99;session.stage(a,data,'textur')
    # A later import composes on the edited bytes instead of discarding the texture.
    data=bytearray(session.current(a));data[-1]=88;session.stage(a,data,'form')
    session.stage(b,b'B'*100,'eyes')
    output,backup=session.save(tmp_path/'output.bin')
    assert backup is None and source.read_bytes()==before
    assert output.stat().st_size==len(before)
    other=EditSession(output,size)
    assert other.original(a)[0]==99 and other.original(a)[-1]==88
    assert other.original(b)==b'B'*100
    raw=output.read_bytes()
    for i in (0,3,5,6,7):assert raw[i*size:(i+1)*size]==before[i*size:(i+1)*size]
    tail=raw[4*size+(24 if size==2352 else 0)+100:4*size+(24 if size==2352 else 0)+2048]
    assert tail==payloads[4][100:]
    if size==2352:assert all(validate_form1_ecc(raw[i*size:(i+1)*size]) for i in range(8))


def test_atomic_overwrite_requires_confirmation_and_keeps_backup(tmp_path):
    image=tmp_path/'game.iso';original=b'A'*4096;image.write_bytes(original)
    session=EditSession(image,2048);entry=Entry('M.BIN',0,20,False);session.stage(entry,b'B'*20)
    with pytest.raises(FileExistsError):session.save(image)
    assert image.read_bytes()==original
    target,backup=session.save(image,overwrite=True)
    assert backup.read_bytes()==original and image.read_bytes()==b'B'*20+original[20:]


def test_changed_source_wrong_size_overlapping_and_noop(tmp_path):
    image=tmp_path/'game.iso';image.write_bytes(b'A'*8192)
    s=EditSession(image,2048);a=Entry('a',0,100,False)
    with pytest.raises(ValueError,match='exakt'):s.stage(a,b'B')
    s.stage(a,b'B'*100)
    with pytest.raises(ValueError,match='Überlappende'):s.stage(Entry('b',0,100,False),b'C'*100)
    s.stage(a,b'A'*100);assert not s.edits
    s.stage(a,b'B'*100);image.write_bytes(b'C'*8192)
    with pytest.raises(ValueError,match='verändert'):s.save(tmp_path/'out.iso')
    assert not (tmp_path/'out.iso').exists()


def test_project_roundtrip_is_atomic_on_wrong_original(tmp_path):
    image=tmp_path/'game.iso';image.write_bytes(b'A'*4096)
    s=EditSession(image,2048);a=Entry('M.BIN',0,100,False);s.stage(a,b'B'*100,'model')
    project=tmp_path/'test.dw2mod';s.export_project(project)
    loaded=EditSession(image,2048);loaded.import_project(project,[a])
    assert loaded.current(a)==b'B'*100
    other=tmp_path/'other.iso';other.write_bytes(b'C'*4096);bad=EditSession(other,2048)
    with pytest.raises(ValueError,match='Originaldatei'):bad.import_project(project,[a])
    assert not bad.edits


def test_write_failure_never_replaces_existing_target(tmp_path,monkeypatch):
    import dw2studio.core.edit_session as module
    image=tmp_path/'game.iso';image.write_bytes(b'A'*4096);out=tmp_path/'out.iso';out.write_bytes(b'OLD')
    s=EditSession(image,2048);s.stage(Entry('M',0,100,False),b'B'*100)
    monkeypatch.setattr(module.os,'replace',lambda *args:(_ for _ in ()).throw(OSError('simulated write failure')))
    with pytest.raises(OSError):s.save(out,overwrite=True)
    assert out.read_bytes()==b'OLD' and image.read_bytes()==b'A'*4096
    assert not list(tmp_path.glob('*.partial'))
