"""Native name pointers, US text encoding, RAW checksums and the real rename UI."""
import struct
from pathlib import Path
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QDialog,QDialogButtonBox,QFileDialog
from dw2studio.core.digimon_names import (NameTable,NameRepository,encode_name,
    decode_name,table_name,discover_tables)
from dw2studio.core.edit_session import EditSession
from dw2studio.core.disc import Entry
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.fast_loading import scan_image
from dw2studio.core.psx_patch import validate_form1_ecc
from test_native_rom_bridge import sector


def table_fixture(names=None,pool_size=128):
    names=names or {3:'Agumon',4:'Betamon',5:'Greymon',12:'MetalGreymon',253:'?????',254:'?????'}
    pool_end=8+pool_size;records_start=pool_end+24
    data=bytearray(records_start+40*(len(names)+1));struct.pack_into('<II',data,0,records_start,pool_end)
    data[pool_end:records_start]=bytes(range(24))  # opaque effect data must survive.
    pointer=8
    for row,(identifier,text) in enumerate(names.items()):
        raw=bytes('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'.index(c) if c in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' else 0x44 if c=='?' else 0x49 for c in text)
        struct.pack_into('<IHH',data,records_start+40*row,pointer,identifier*2,identifier+100)
        data[records_start+40*row+8:records_start+40*row+40]=bytes([row+1])*32
        data[pointer:pointer+len(raw)+1]=raw+b'\xff';pointer+=(len(raw)+1+3)//4*4
    assert pointer<=pool_end
    return bytes(data)


def image_fixture(tmp_path,raw=False,table=None):
    data=table or table_fixture();payload=[bytearray(2048) for _ in range(24)]
    payload[16][0:6]=b'\1CD001';struct.pack_into('<I',payload[16],158,19);struct.pack_into('<I',payload[16],166,2048)
    payload[6][:len(data)]=data;payload[3][:16]=b'MODEL0123456789!'
    image=tmp_path/('game.bin' if raw else 'game.iso')
    image.write_bytes(b''.join(sector(i,bytes(p)) for i,p in enumerate(payload)) if raw else b''.join(payload))
    entry=Entry('AAA/4.AAA/DATAFILE/MODELDT0.BIN',6,len(data),False)
    return image,entry,data


def test_us_character_codes_from_reference():
    assert encode_name('Agumon')==bytes.fromhex('0a2a38303231')
    assert encode_name('MetalGreymon')==bytes.fromhex('162837242f1035283c303231')
    assert encode_name('A - 9')==bytes([10,253,73,253,9])
    assert decode_name(encode_name("A&/?!.,':+"))=="A&/?!.,':+"


@pytest.mark.parametrize('text',['',' ',' Test','Test ','ämon','Pokémon','A\nB','A\xffB','A'*14])
def test_unsupported_or_overlong_names_rejected(text):
    with pytest.raises(ValueError):encode_name(text)


def test_in_place_shorter_longer_and_untouched_records():
    original=table_fixture();table=NameTable(original)
    assert table.record(3).text=='Agumon'
    changed=table.renamed(3,'Feuerdrache');again=NameTable(changed)
    assert len(changed)==len(original) and again.record(3).text=='Feuerdrache'
    assert all(again.record(i).text==row.text for i,row in table.records.items() if i!=3)
    assert changed[table.pool_end:table.records_start]==original[table.pool_end:table.records_start]
    for r in table.order:assert changed[r.row+4:r.row+40]==original[r.row+4:r.row+40]
    assert table.renamed(3,'Agumon')==original
    assert NameTable(again.renamed(3,'X')).record(3).text=='X'


def test_repacking_deduplicates_names_but_alias_edits_remain_independent():
    # Exactly full pool: a long new name fits only after sharing duplicate strings.
    original=table_fixture({3:'Agumon',4:'Betamon',253:'?????',254:'?????'},pool_size=32)
    table=NameTable(original);changed=table.renamed(3,'Feuerdrache');after=NameTable(changed)
    assert after.record(3).text=='Feuerdrache' and after.record(4).text=='Betamon'
    assert after.record(253).pointer==after.record(254).pointer
    final=NameTable(after.renamed(253,'X'))
    assert final.record(254).text=='?????' and final.record(253).text=='X'


def test_insufficient_pool_and_malformed_data_never_write(tmp_path):
    data=table_fixture({3:'Agumon',4:'Betamon'},pool_size=16)
    with pytest.raises(ValueError,match='Namensspeicher'):NameTable(data).renamed(3,'Feuerdrache')
    cases=[]
    bad=bytearray(data);struct.pack_into('<I',bad,0,len(data)+4);cases.append(bad)
    bad=bytearray(data);struct.pack_into('<I',bad,NameTable(data).records_start,4);cases.append(bad)
    bad=bytearray(data);bad[8]=0xF0;cases.append(bad)
    bad=bytearray(data);bad[15]=0x41;cases.append(bad)  # opaque byte in alignment padding.
    for value in cases:
        with pytest.raises(ValueError):NameTable(value)
    assert table_name(3)=='MODELDT0.BIN' and table_name(300)=='MODELDT1.BIN' and table_name(400)=='MODELDT2.BIN'


@pytest.mark.parametrize('raw',[False,True])
def test_multiple_names_plus_model_one_fixed_size_image_export(tmp_path,raw):
    image,entry,data=image_fixture(tmp_path,raw);before=image.read_bytes();session=EditSession(image,2352 if raw else 2048);entries=[entry]
    repo=NameRepository(session,entries);repo.rename(3,'Feuerdrache');repo.rename(4,'Wassermon');repo.rename(3,'Flammenmon')
    model=Entry('M003AGUM.BIN',3,16,False);session.stage(model,b'NEW-MODEL1234567','Modell')
    assert len(session.edits)==2 and image.read_bytes()==before
    project=tmp_path/'names.dw2mod';session.export_project(project)
    reopened=EditSession(image,session.sector_size);NameRepository(reopened,entries);reopened.import_project(project,entries+[model])
    assert NameRepository(reopened,entries).names()[3]=='Flammenmon'
    output,_=reopened.save(tmp_path/('out.bin' if raw else 'out.iso'))
    after=EditSession(output,session.sector_size);native=NameTable(after.current(entry))
    assert native.record(3).text=='Flammenmon' and native.record(4).text=='Wassermon'
    assert output.stat().st_size==len(before) and image.read_bytes()==before
    assert after.current(model)==b'NEW-MODEL1234567'
    if raw:
        stream=output.read_bytes();assert all(validate_form1_ecc(stream[i*2352:(i+1)*2352]) for i in range(24))
    entries.append(model)
    _,catalog,_=scan_image(output,tmp_path/'cache',lambda *args:entries)
    assert catalog[0].name=='Flammenmon'  # reopening does not use the bundled old catalogue name.


def test_restoring_individual_names_preserves_other_edits_and_final_restore_is_exact(tmp_path):
    image,entry,data=image_fixture(tmp_path,table=table_fixture({3:'Agumon',4:'Betamon',253:'?????',254:'?????'},pool_size=32))
    session=EditSession(image,2048);repo=NameRepository(session,[entry]);repo.rename(3,'Feuerdrache');repo.rename(4,'Wassermon')
    repo.rename(3,repo.original_name(3));assert repo.names()[3]=='Agumon' and repo.names()[4]=='Wassermon' and session.edits
    repo.rename(4,repo.original_name(4));assert session.current(entry)==data and not session.edits


def test_ambiguous_same_filename_at_different_allocations_is_blocked(tmp_path):
    image,entry,_=image_fixture(tmp_path);session=EditSession(image,2048)
    with pytest.raises(ValueError,match='mehrfach'):NameRepository(session,[entry,Entry('OTHER/MODELDT0.BIN',8,entry.size,False)])
    alias=Entry('RECOVERED/MODELDT0.BIN',entry.lba,entry.size,False)
    assert len(NameRepository(session,[entry,alias]).entries)==1
    with pytest.raises(ValueError,match='nicht eindeutig'):NameRepository(session,[]).rename(3,'Testmon')


def test_private_us_index_fallback_uses_verified_name_table_allocation(tmp_path):
    size=2048;image=tmp_path/'hidden.iso';data=bytearray(530*size);exe=bytearray(651264);exe[:8]=b'PS-X EXE';name_data=table_fixture()
    struct.pack_into('<I',exe,0x33F94+3257*4,500);struct.pack_into('<H',exe,0x37900+3257*2,1)
    data[24*size:24*size+len(exe)]=exe;data[500*size:500*size+len(name_data)]=name_data;image.write_bytes(data)
    entries=[Entry('SLUS_011.93',24,len(exe),False)];session=EditSession(image,2048);repo=NameRepository(session,entries)
    assert repo.lookup(3)[0].lba==500 and any(e.path=='INTERNAL/MODELDT0.BIN' for e in entries)
    repo.rename(3,'Testmon');assert session.edits and image.read_bytes()==data
    corrupt=bytearray(exe);struct.pack_into('<I',corrupt,0x33F94+3257*4,999999);data[24*size:24*size+len(corrupt)]=corrupt;image.write_bytes(data)
    with pytest.raises(ValueError,match='außerhalb'):discover_tables(EditSession(image,2048),entries[:1])


def setup_window(window,tmp_path):
    image,entry,data=image_fixture(tmp_path);window.image=str(image);window.image_path=image;window.index_key='test';window.session=EditSession(image,2048);window.entries=[entry]
    window.catalog=[DigimonCandidate(3,'AGUM','Agumon'),DigimonCandidate(4,'BETA','Betamon')];window._source_names={3:'Agumon',4:'Betamon'};window.refresh_list();window.update_actions()
    return image,entry,data


def test_button_opens_native_name_dialog_before_model_load_and_updates_filtered_list(window,tmp_path,monkeypatch,qapp):
    from dw2studio.gui.name_dialog import RenameDialog
    image,entry,data=setup_window(window,tmp_path);before=image.read_bytes();window.search.setText('Agumon');seen=[]
    def exec_dialog(dialog):
        seen.append(dialog);assert dialog.name_edit.maxLength()==13
        dialog.name_edit.setText('Feuerdrache');dialog.accept();return dialog.result()
    monkeypatch.setattr(RenameDialog,'exec',exec_dialog);monkeypatch.setattr(window,'load_digimon',lambda:pytest.fail('Renaming must not reload 3D geometry'))
    window.show();qapp.processEvents();assert window.rename_button.isEnabled()
    QTest.mouseClick(window.rename_button,Qt.MouseButton.LeftButton)
    assert seen and not window.test_errors and window.current.id==3 and window.current.name=='Feuerdrache'
    assert window.search.text()=='' and 'Feuerdrache' in window.digimon.item(0).text()
    assert NameTable(window.session.current(entry)).record(3).text=='Feuerdrache'
    assert image.read_bytes()==before and window.pending.count()==1


def test_dialog_validation_cancel_and_source_name_reset(qapp,tmp_path):
    from dw2studio.gui.name_dialog import RenameDialog
    table=NameTable(table_fixture());dialog=RenameDialog(3,table,'MODELDT0.BIN','Agumon');button=dialog.buttons.button(QDialogButtonBox.StandardButton.Save)
    assert not button.isEnabled();dialog.name_edit.setText('Füchse');assert not button.isEnabled()
    dialog.name_edit.setText('Testmon');assert button.isEnabled();dialog.reject();assert dialog.result()==QDialog.DialogCode.Rejected
    assert table.record(3).text=='Agumon'


def test_project_load_refreshes_names_and_bad_native_name_project_rolls_back(window,tmp_path,monkeypatch):
    image,entry,data=setup_window(window,tmp_path);source=EditSession(image,2048);NameRepository(source,[entry]).rename(3,'Feuerdrache');project=tmp_path/'names.dw2mod';source.export_project(project)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args,**kwargs:(str(project),''));monkeypatch.setattr(window,'load_digimon',lambda:None)
    window.load_project();assert window.catalog[0].name=='Feuerdrache' and not window.test_errors
    before=window.session.edits.copy();bad=bytearray(data);bad[8]=0xF0;source.stage(entry,bad);source.export_project(project)
    window.load_project();assert window.test_errors and window.session.edits==before and window.catalog[0].name=='Feuerdrache'
