import sqlite3
from unittest.mock import patch

import pytest

from database.migrations_work_learning_magc1_wave2 import TABLES, apply_magc1_wave2_schema
import services.services_work_learning_programs as p05
import services.services_work_learning_authority as p09
from services.services_work_learning_provenance import _wave1_source_context


@pytest.fixture()
def env(tmp_path):
    path = tmp_path / "wave2.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
      CREATE TABLE hub_programs(program_id TEXT PRIMARY KEY,workspace_id TEXT,firm_id TEXT,owner_id TEXT);
      CREATE TABLE hub_program_source_references(source_reference_id TEXT PRIMARY KEY,program_id TEXT,issue_id TEXT);
      CREATE TABLE hub_program_source_metadata(metadata_id TEXT PRIMARY KEY,program_id TEXT,source_reference_id TEXT,created_at TEXT);
      INSERT INTO hub_programs VALUES('P1','W1','F1','O1');
      INSERT INTO hub_programs VALUES('P2','W2','F2','O2');
      INSERT INTO hub_program_source_references VALUES('S1','P1','');
      INSERT INTO hub_program_source_references VALUES('S2','P1','');
      INSERT INTO hub_program_source_references VALUES('SX','P2','');
      INSERT INTO hub_program_source_metadata VALUES('M1','P1','S1','now');
    """)
    conn.commit(); conn.close()
    apply_magc1_wave2_schema(path)

    def connection():
        item=sqlite3.connect(path); item.row_factory=sqlite3.Row; return item
    def program(**kw):
        item=connection(); row=item.execute("SELECT * FROM hub_programs WHERE program_id=? AND firm_id=? AND owner_id=?",(kw['program_id'],kw['firm_id'],kw['owner_id'])).fetchone(); item.close()
        return dict(row) if row else None
    with patch.object(p05,'get_connection',side_effect=connection), patch.object(p09,'get_connection',side_effect=connection), patch.object(p09,'get_hub_program',side_effect=program):
        yield path


def hierarchy(**changes):
    values=dict(firm_id='F1',context_type='PROGRAM',context_id='P1',subject='governing law',
        hierarchy_kind='CONTROLLING_LAW',source_reference_id='S1',hierarchy_state='UNRESOLVED',
        applicability_jurisdiction=None,basis='reviewed materials',provenance='work log',
        decision_origin='SYSTEM_SUGGESTED',human_confirmed=False,actor='system',actor_capacity='assistant')
    values.update(changes); return p09.record_authority_hierarchy_determination(**values)


def test_migration_additive_idempotent_empty_and_no_shadow_registries(env):
    path=env
    assert apply_magc1_wave2_schema(path)=={'schema_complete':True,'records_created':0}
    conn=sqlite3.connect(path)
    assert all(conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==0 for table in TABLES)
    names={row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not {'hub_authority_conflicts','hub_governing_laws','hub_governing_instruments','hub_document_registry','hub_instrument_registry'} & names
    conn.close()


def test_generic_hierarchy_safety_and_no_inference(env):
    for context in p09.CONTEXT_TYPES:
        assert hierarchy(context_type=context,context_id='external-'+context).startswith('HIER-')
    with pytest.raises(ValueError,match='source_not_available'):
        hierarchy(source_reference_id='missing',context_id='missing')
    with pytest.raises(ValueError,match='machine_hierarchy'):
        hierarchy(hierarchy_state='CONTROLLING',applicability_jurisdiction='NJ')
    with pytest.raises(ValueError,match='human_confirmation'):
        hierarchy(hierarchy_state='CONTROLLING',applicability_jurisdiction='NJ',decision_origin='PROFESSIONAL')
    with pytest.raises(ValueError,match='jurisdiction_required'):
        hierarchy(hierarchy_state='CONTROLLING',decision_origin='PROFESSIONAL',human_confirmed=True)


def test_governing_instrument_identity_and_predecessor_rules(env):
    unresolved=hierarchy(hierarchy_kind='GOVERNING_INSTRUMENT',hierarchy_state='CONTROLLING',
        applicability_jurisdiction='NJ',decision_origin='PROFESSIONAL',human_confirmed=True)
    assert p09.get_authority_hierarchy_history(firm_id='F1',context_type='PROGRAM',context_id='P1',subject='governing law',hierarchy_kind='GOVERNING_INSTRUMENT')[0]['hierarchy_state']=='UNRESOLVED'
    with pytest.raises(ValueError,match='instrument_object_type'):
        hierarchy(context_id='bad-object',hierarchy_kind='GOVERNING_INSTRUMENT',document_object_type='INSTRUMENT',document_object_id='I1')
    first=hierarchy(context_id='history',decision_origin='PROFESSIONAL',human_confirmed=True,hierarchy_state='CONTROLLING',applicability_jurisdiction='NJ')
    with pytest.raises(ValueError,match='prior_hierarchy'):
        hierarchy(context_id='other',hierarchy_state='SUPERSEDED',decision_origin='PROFESSIONAL',prior_hierarchy_id=first)
    second=hierarchy(context_id='history',hierarchy_state='SUPERSEDED',decision_origin='PROFESSIONAL',prior_hierarchy_id=first)
    assert second != first and unresolved


def test_existing_document_and_generated_document_references_are_accepted(env):
    conn=sqlite3.connect(env)
    conn.executescript("""CREATE TABLE documents(document_id TEXT,firm_id TEXT);
      CREATE TABLE generated_documents(document_id TEXT);
      INSERT INTO documents VALUES('D1','F1');
      INSERT INTO generated_documents VALUES('G1');""")
    conn.commit(); conn.close()
    for object_type,object_id in (('DOCUMENT','D1'),('GENERATED_DOCUMENT','G1')):
        hid=hierarchy(context_id=object_id,hierarchy_kind='GOVERNING_INSTRUMENT',
            hierarchy_state='CONTROLLING',applicability_jurisdiction='NJ',
            decision_origin='PROFESSIONAL',human_confirmed=True,
            document_object_type=object_type,document_object_id=object_id)
        row=p09.get_authority_hierarchy_history(firm_id='F1',context_type='PROGRAM',context_id=object_id,subject='governing law',hierarchy_kind='GOVERNING_INSTRUMENT')[0]
        assert row['hierarchy_id']==hid and row['hierarchy_state']=='CONTROLLING'


def test_conflict_composition_is_read_only_and_selects_no_winner(env):
    args=dict(context_id='conflict',hierarchy_state='CONTROLLING',decision_origin='PROFESSIONAL',human_confirmed=True,applicability_jurisdiction='NJ')
    hierarchy(**args); hierarchy(**{**args,'source_reference_id':'S2'})
    path=env; before=path.read_bytes()
    result=p09.compose_authority_hierarchy_state(firm_id='F1',context_type='PROGRAM',context_id='conflict',subject='governing law',hierarchy_kind='CONTROLLING_LAW')
    assert result['hierarchy_state']=='UNRESOLVED' and result['winner'] is None and result['review_required']
    assert path.read_bytes()==before


def test_change_check_and_generic_impact_machine_rules(env):
    with pytest.raises(ValueError,match='source_not_available'):
        p05.record_source_change_check(program_id='P1',firm_id='F1',owner_id='O1',source_reference_id='missing',observation_state='UNRESOLVED',basis='b',provenance='p',actor='a',actor_capacity='c')
    check=p05.record_source_change_check(program_id='P1',firm_id='F1',owner_id='O1',source_reference_id='S1',metadata_id='M1',observation_state='CHANGE_DETECTED',basis='comparison',provenance='copy',actor='a',actor_capacity='reviewer')
    for context in p09.CONTEXT_TYPES:
        p09.record_authority_change_impact(firm_id='F1',context_type=context,context_id=context,subject='review',source_reference_id='S1',change_check_id=check,impact_state='REVIEW_REQUIRED',basis='change observed',provenance='check',decision_origin='SYSTEM_SUGGESTED',actor='system',actor_capacity='assistant')
    with pytest.raises(ValueError,match='machine_change_impact'):
        p09.record_authority_change_impact(firm_id='F1',context_type='PROGRAM',context_id='x',subject='review',source_reference_id='S1',change_check_id=check,impact_state='NO_IMPACT',basis='b',provenance='p',decision_origin='SYSTEM_SUGGESTED',actor='system',actor_capacity='assistant')


def test_p08_wave2_optional_read_is_read_only_and_absence_safe(env,tmp_path):
    hierarchy(context_id='derived')
    check=p05.record_source_change_check(program_id='P1',firm_id='F1',owner_id='O1',source_reference_id='S1',observation_state='UNRESOLVED',basis='b',provenance='p',actor='a',actor_capacity='c')
    p09.record_authority_change_impact(firm_id='F1',context_type='PROGRAM',context_id='derived',subject='review',source_reference_id='S1',change_check_id=check,impact_state='UNRESOLVED',basis='b',provenance='p',decision_origin='SYSTEM_SUGGESTED',actor='a',actor_capacity='c')
    path=env; before=path.read_bytes(); derived=_wave1_source_context(path,['S1'],'F1')
    assert derived['authority_hierarchy_determinations'] and derived['source_change_checks'] and derived['authority_change_impacts']
    assert path.read_bytes()==before
    old=tmp_path/'old.db'; sqlite3.connect(old).close()
    assert 'authority_hierarchy_determinations' not in _wave1_source_context(old,['S1'],'F1')


def test_append_only_triggers(env):
    hierarchy(context_id='locked')
    check=p05.record_source_change_check(program_id='P1',firm_id='F1',owner_id='O1',source_reference_id='S1',observation_state='UNRESOLVED',basis='b',provenance='p',actor='a',actor_capacity='c')
    p09.record_authority_change_impact(firm_id='F1',context_type='PROGRAM',context_id='locked',subject='review',source_reference_id='S1',change_check_id=check,impact_state='UNRESOLVED',basis='b',provenance='p',decision_origin='SYSTEM_SUGGESTED',actor='a',actor_capacity='c')
    conn=sqlite3.connect(env)
    for table in TABLES:
        with pytest.raises(sqlite3.IntegrityError,match='append_only'):
            conn.execute(f'UPDATE {table} SET created_at=created_at')
        conn.rollback()
    conn.close()
