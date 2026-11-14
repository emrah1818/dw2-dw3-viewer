"""US DW2 private-table relocation with real ISO records and RAW ECC."""
import struct,json
from pathlib import Path
import pytest
from PyQt6.QtWidgets import QDialog,QFileDialog
from dw2studio.core.disc import Disc,Entry
from dw2studio.core.edit_session import EditSession
from dw2studio.core.dw2_file_index import US,read_index
from dw2studio.core import digimon_transfer as dt
from dw2studio.core.native_relocation import layout
from dw2studio.core.native_model import NativeModel
from dw2studio.core.rig_animation import NativeAnimation
from dw2studio.core.catalog import DigimonCandidate
from test_rig_import_v8 import native_model,animation_bytes,project
from test_digimon_transfer_v36 import animation


def record(name,lba,size,directory=False):
    name=name if isinstance(name,bytes) else (name+';1').encode()
    n=33+len(name);n+=n%2;out=bytearray(n);out[0]=n
    out[2:10]=struct.pack('<I',lba)+struct.pack('>I',lba)
    out[10:18]=struct.pack('<I',size)+struct.pack('>I',size)
    out[25]=2 if directory else 0;out[28:32]=b'\x01\0\0\x01';out[32]=len(name);out[33:33+len(name)]=name
    return out


def image_fixture(tmp_path,raw=False):
    data=bytearray(520*2048);pvd=bytearray(2048);pvd[:7]=b'\x01CD001\x01'
    pvd[80:88]=struct.pack('<I',520)+struct.pack('>I',520)
    pvd[128:132]=b'\0\x08\x08\0';pvd[156:190]=record(b'\0',20,2048,True)
    data[16*2048:17*2048]=pvd;data[17*2048:17*2048+7]=b'\xffCD001\x01'
    data[24*2048:24*2048+8]=b'PS-X EXE'
    target_model=native_model(bones=2,tim=256);target_anim=animation(2)
    donor_model=native_model(bones=2,tim=512)
    start=struct.unpack_from('<I',donor_model)[0];delta=15000
    donor_model=bytearray(donor_model[:start]+bytes(delta)+donor_model[start:]);struct.pack_into('<II',donor_model,0,start+delta,0)
    files={'M':bytes(donor_model),'A':animation_bytes()}
    native=[('M023YUKI.BIN',400,target_model,103),('A023YUKI.BIN',410,target_anim,13),
            ('M005GREY.BIN',420,files['M'],94),('A005GREY.BIN',440,files['A'],3)]
    directory=record(b'\0',20,2048,True)+record(b'\1',20,2048,True)+record('SLUS_011.93',24,318*2048)
    for name,lba,content,index in native:
        data[lba*2048:lba*2048+len(content)]=content
        directory+=record(name,lba,len(content))
        struct.pack_into('<I',data,24*2048+US[1]+index*4,lba)
        struct.pack_into('<H',data,24*2048+US[2]+index*2,(len(content)+2047)//2048)
    data[20*2048:20*2048+len(directory)]=directory
    data[500*2048:501*2048]=b'unrelated asset'.ljust(2048,b'!')
    if raw:
        from test_native_rom_bridge import sector
        content=b''.join(sector(i,data[i*2048:(i+1)*2048]) for i in range(520))
    else:content=bytes(data)
    path=tmp_path/('game.bin' if raw else 'game.iso');path.write_bytes(content)
    with_disc=Disc(path)
    try:entries=with_disc.entries.copy()
    finally:with_disc.close()
    targets=[e for e in entries if '023YUKI' in e.path]
    return EditSession(path,2352 if raw else 2048),entries,targets,files,content


def transfer(files):return dt.Transfer({'name':'Greymon','id':5,'code':'GREY'},files,{})


@pytest.mark.parametrize('raw',[False,True])
def test_bigger_model_and_animation_are_relocated_and_both_tables_updated(tmp_path,raw):
    session,entries,targets,files,original=image_fixture(tmp_path,raw)
    plan=dt.plan_transfer(transfer(files),targets,session)
    assert not plan.errors and len(plan.relocated)==2
    dt.apply_plan(plan,session)
    assert session.source.read_bytes()==original
    out,_=session.save(tmp_path/('larger.bin' if raw else 'larger.iso'))
    disc=Disc(out)
    try:
        for old in targets:
            new=next(e for e in disc.entries if e.path==old.path)
            assert new.lba>=520 and new.size>old.size
            expected=session.current(old)
            assert disc.read(new.lba,new.size)==expected
            # Loader table matches ISO metadata, not just the viewer override.
            backend=layout(EditSession(out,session.sector_size));idx,_=backend.target(new)
            assert backend.entries[idx]==(new.lba,(new.size+2047)//2048)
        assert disc.sector(500)==b'unrelated asset'.ljust(2048,b'!')
        assert int.from_bytes(disc.sector(16)[80:84],'little')==disc.sector_count
        # Original donor and old target extents remain independent and unchanged.
        olddisc=Disc(session.source)
        try:
            for old in entries:
                if '023YUKI' in old.path or '005GREY' in old.path:assert disc.read(old.lba,old.size)==olddisc.read(old.lba,old.size)
        finally:olddisc.close()
    finally:disc.close()
    if raw:
        private=read_index(out)
        for key,(lba,size,index) in session.last_relocations.items():assert (private[index].lba,private[index].sectors)==(lba,(size+2047)//2048)
    assert out.stat().st_size>len(original) and session.source.read_bytes()==original


def test_pending_texture_edit_and_mod_project_preserve_larger_file(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path)
    dt.apply_plan(dt.plan_transfer(transfer(files),targets,session),session)
    m=next(e for e in targets if e.path.startswith('M'));data=bytearray(session.current(m))
    # A palette change after a full-model import must not revert to the old size.
    start=NativeModel(data).tim_start;data[start+16448-2:start+16448]=b'\x1f\x00'
    session.stage(m,bytes(data),'PNG changed')
    assert session.edits[(m.path,m.lba)].relocate
    project=tmp_path/'working.dw2mod';session.export_project(project)
    restored=EditSession(session.source,2048);restored.import_project(project,entries)
    assert restored.edits==session.edits
    out,_=restored.save(tmp_path/'restored.iso')
    d=Disc(out)
    try:
        e=next(e for e in d.entries if e.path==m.path);assert d.read(e.lba,e.size)==bytes(data)
    finally:d.close()


def test_second_swap_and_native_edit_after_reopening_use_new_locations(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path)
    dt.apply_plan(dt.plan_transfer(transfer(files),targets,session),session)
    out,_=session.save(tmp_path/'first.iso');d=Disc(out)
    try:new_entries=d.entries.copy()
    finally:d.close()
    second=EditSession(out,2048);new_targets=[e for e in new_entries if '023YUKI' in e.path]
    m=next(e for e in new_targets if e.path.startswith('M'));edited=bytearray(second.current(m));edited[-2:]=b'\x10\x01'
    second.stage(m,edited,'texture edit');new,_=second.save(tmp_path/'second.iso')
    check=Disc(new)
    try:
        target=next(e for e in check.entries if e.path==m.path);donor=next(e for e in check.entries if 'M005GREY' in e.path)
        assert check.read(target.lba,target.size)==bytes(edited)
        assert check.read(donor.lba,donor.size)==files['M']
    finally:check.close()


def test_overwrite_makes_original_backup_before_growing_image(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path)
    dt.apply_plan(dt.plan_transfer(transfer(files),targets,session),session)
    out,backup=session.save(session.source,overwrite=True)
    assert backup.read_bytes()==original and out.stat().st_size>len(original)


@pytest.mark.parametrize('fault',['exe','ambiguous','directory'])
def test_unknown_or_ambiguous_layout_cannot_stage_large_data(tmp_path,fault):
    session,entries,targets,files,original=image_fixture(tmp_path)
    path=session.source;data=bytearray(path.read_bytes())
    if fault=='exe':data[24*2048:24*2048+8]=b'NOTEXE00'
    elif fault=='ambiguous':
        struct.pack_into('<I',data,24*2048+US[1]+1200*4,targets[0].lba)
        struct.pack_into('<H',data,24*2048+US[2]+1200*2,(targets[0].size+2047)//2048)
        struct.pack_into('<I',data,24*2048+US[1]+103*4,500)
    else:
        at=data.index(b'M023YUKI.BIN;1')-33;struct.pack_into('>I',data,at+6,1)
    path.write_bytes(data);session=EditSession(path,2048)
    plan=dt.plan_transfer(transfer(files),targets,session)
    assert plan.errors
    with pytest.raises(ValueError):dt.apply_plan(plan,session)
    assert not session.edits and path.read_bytes()==bytes(data)


def test_gui_swap_then_image_written_refreshes_entry_sizes(window,tmp_path,monkeypatch):
    from dw2studio.core.model_replacements import clear_replacement
    from test_digimon_transfer_v36 import donor
    session,entries,targets,files,original=image_fixture(tmp_path)
    scene,_,_=donor(tmp_path);payload=dt.make_payload(type('S',(),{'id':5,'code':'GREY','name':'Greymon'})(),files)
    exported=tmp_path/'greymon.glb';dt.export_exchange(scene,exported,payload)
    c=DigimonCandidate(23,'YUKI','Frigimon',targets)
    window.session=session;window.image=str(session.source);window.image_path=session.source;window.entries=entries;window.catalog=[c];window.current=c
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(exported),''))
    monkeypatch.setattr(QDialog,'exec',lambda dialog:QDialog.DialogCode.Accepted)
    monkeypatch.setattr(window,'load_digimon',lambda:None)
    window.replace_digimon()
    assert not window.test_errors and len(window.session.edits)==2
    assert window.transfer_dialog.confirm.isEnabled()
    old_lba=targets[0].lba
    out,_=session.save(tmp_path/'gui.iso');window.image_written(str(out),'')
    assert targets[0].lba!=old_lba and targets[0].size>16708
    assert len(window.session.current(targets[0]))==targets[0].size
    assert not window.session.edits


def test_iso_temporary_file_with_raw_divisible_size_is_still_verified_as_iso(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path)
    appended_count=sum((len(data)+2047)//2048 for data in files.values())
    # Force output length to be divisible by BOTH 2048 and 2352. Filename
    # heuristics must not reinterpret the temporary ISO as a RAW BIN.
    padding=(-520-appended_count)%147
    with session.source.open('ab') as handle:handle.write(bytes(padding*2048))
    session=EditSession(session.source,2048)
    dt.apply_plan(dt.plan_transfer(transfer(files),targets,session),session)
    out,_=session.save(tmp_path/'ambiguous.iso')
    assert out.stat().st_size%2352==0
    assert layout(EditSession(out,2048)).target(Entry('M023YUKI.BIN',*session.last_relocations[('M023YUKI.BIN',400)][:2],False))


def test_documented_file_ids_allow_independent_edit_of_shared_native_extent(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path);data=bytearray(original)
    m=next(e for e in targets if e.path.startswith('M'))
    count=(m.size+2047)//2048
    for index in (103,94):
        struct.pack_into('<I',data,24*2048+US[1]+index*4,0);struct.pack_into('<H',data,24*2048+US[2]+index*2,0)
    # Real US IDs: Frigimon M=103 and Greymon M=94.
    for index in (103,94):
        struct.pack_into('<I',data,24*2048+US[1]+index*4,m.lba);struct.pack_into('<H',data,24*2048+US[2]+index*2,count)
    pos=data.index(b'M005GREY.BIN;1')-33
    data[pos+2:pos+10]=struct.pack('<I',m.lba)+struct.pack('>I',m.lba)
    data[pos+10:pos+18]=struct.pack('<I',m.size)+struct.pack('>I',m.size)
    session.source.write_bytes(data);session=EditSession(session.source,2048)
    edited=bytearray(session.current(m));edited[-4:]=b'\x1f\x00\x20\x00'
    session.stage(m,edited,'PNG edit')
    assert session.edits[(m.path,m.lba)].relocate
    out,_=session.save(tmp_path/'independent.iso');disc=Disc(out)
    try:
        target=next(e for e in disc.entries if e.path=='M023YUKI.BIN');source=next(e for e in disc.entries if e.path=='M005GREY.BIN')
        assert target.lba!=source.lba and disc.read(target.lba,target.size)==bytes(edited)
        assert disc.read(source.lba,source.size)==bytes(data[m.lba*2048:m.lba*2048+m.size])
    finally:disc.close()


def test_save_failure_does_not_publish_half_written_larger_image(tmp_path,monkeypatch):
    session,entries,targets,files,original=image_fixture(tmp_path)
    dt.apply_plan(dt.plan_transfer(transfer(files),targets,session),session)
    out=tmp_path/'fail.iso'
    def fail(*args):raise OSError('simulated final publication error')
    monkeypatch.setattr('dw2studio.core.edit_session.os.link',fail)
    with pytest.raises(OSError):session.save(out)
    assert not out.exists() and not list(tmp_path.glob('*.partial'))
    assert session.source.read_bytes()==original


def test_matching_size_swap_stays_in_place_and_does_not_grow_image(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path)
    new={r:session.current(next(e for e in targets if e.path.startswith(r))) for r in ('M','A')}
    model=bytearray(new['M']);end=dt._texture_end(NativeModel(model));model[end-2:end]=b'\x1f\x00';new['M']=bytes(model)
    plan=dt.plan_transfer(transfer(new),targets,session)
    assert not plan.errors and not plan.relocated
    dt.apply_plan(plan,session);out,_=session.save(tmp_path/'same_size.iso')
    assert out.stat().st_size==len(original) and not session.last_relocations


def test_reported_greymon_frigimon_sizes_and_bone_counts_no_longer_block(tmp_path):
    session,entries,targets,files,original=image_fixture(tmp_path);data=bytearray(original)
    # Same M/A byte sizes and 20/12 skeleton counts as the user's screenshot;
    # all geometry/frames are newly generated synthetic data.
    source_model=bytearray(native_model(bones=20,tim=13204)[:-4]);struct.pack_into('<I',source_model,4,0)
    target_model=bytearray(native_model(bones=12,tim=10868)[:-4]);struct.pack_into('<I',target_model,4,0)
    source_anim=animation(20,1).ljust(20095,b'\0')+b'\x01'
    target_anim=animation(12,1).ljust(9639,b'\0')+b'\x01'
    native=[('M023YUKI.BIN',400,bytes(target_model),103),('A023YUKI.BIN',415,target_anim,13),
            ('M005GREY.BIN',420,bytes(source_model),94),('A005GREY.BIN',440,source_anim,3)]
    for name,lba,content,index in native:
        data[lba*2048:lba*2048+len(content)]=content
        pos=data.index(name.encode()+b';1')-33
        data[pos+2:pos+10]=struct.pack('<I',lba)+struct.pack('>I',lba)
        data[pos+10:pos+18]=struct.pack('<I',len(content))+struct.pack('>I',len(content))
        struct.pack_into('<I',data,24*2048+US[1]+index*4,lba);struct.pack_into('<H',data,24*2048+US[2]+index*2,(len(content)+2047)//2048)
    session.source.write_bytes(data);session=EditSession(session.source,2048)
    targets=[Entry(n,l,len(b),False) for n,l,b,i in native[:2]]
    plan=dt.plan_transfer(transfer({'M':bytes(source_model),'A':source_anim}),targets,session)
    assert not plan.errors and plan.source_bones==20 and plan.target_bones==12
    assert [row[1:3] for row in plan.rows]==[(29652,27316),(20096,9640)]
    assert len(plan.relocated)==2
    dt.apply_plan(plan,session);out,_=session.save(tmp_path/'reported_sizes.iso')
    disc=Disc(out)
    try:
        model=next(e for e in disc.entries if e.path=='M023YUKI.BIN');anim=next(e for e in disc.entries if e.path=='A023YUKI.BIN')
        assert disc.read(model.lba,model.size)==bytes(source_model)
        assert disc.read(anim.lba,anim.size)==source_anim
    finally:disc.close()
