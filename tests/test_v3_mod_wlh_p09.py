import sqlite3
from pathlib import Path
from unittest.mock import patch
import pytest
from database.migrations_work_learning_authority import TABLES,apply_work_learning_authority_schema
import services.services_work_learning_authority as p09

@pytest.fixture()
def env(tmp_path):
 path=tmp_path/'p09.db'; apply_work_learning_authority_schema(path); c=sqlite3.connect(path)
 c.executescript("""CREATE TABLE hub_programs(program_id TEXT PRIMARY KEY,workspace_id TEXT,firm_id TEXT,owner_id TEXT); CREATE TABLE hub_program_issues(issue_id TEXT PRIMARY KEY,program_id TEXT,statement TEXT,created_at TEXT); CREATE TABLE hub_program_source_references(source_reference_id TEXT PRIMARY KEY,program_id TEXT,issue_id TEXT,source_label TEXT,created_at TEXT); INSERT INTO hub_programs VALUES('P1','W1','F1','O1'); INSERT INTO hub_programs VALUES('P2','W2','F2','O2'); INSERT INTO hub_program_issues VALUES('I1','P1','issue','now'); INSERT INTO hub_program_issues VALUES('I2','P1','issue 2','now'); INSERT INTO hub_program_issues VALUES('IX','P2','other','now'); INSERT INTO hub_program_source_references VALUES('S1','P1','','source','now'); INSERT INTO hub_program_source_references VALUES('S2','P1','I1','issue source','now'); INSERT INTO hub_program_source_references VALUES('S3','P1','I2','disconnected source','now'); INSERT INTO hub_program_source_references VALUES('SX','P2','','other','now');"""); c.commit(); c.close()
 def conn(): x=sqlite3.connect(path); x.row_factory=sqlite3.Row; return x
 def program(**kw):
  x=conn(); r=x.execute('SELECT * FROM hub_programs WHERE program_id=? AND firm_id=? AND owner_id=?',(kw['program_id'],kw['firm_id'],kw['owner_id'])).fetchone(); x.close(); return dict(r) if r else None
 with patch.object(p09,'get_connection',side_effect=conn),patch.object(p09,'get_hub_program',side_effect=program): yield path,dict(program_id='P1',workspace_id='W1',firm_id='F1',owner_id='O1')

def classify(scope,**kw): return p09.classify_source_authority(**scope,source_reference_id=kw.pop('source_reference_id','S1'),authority_tier=kw.pop('authority_tier',p09.SOURCE_TIERS[0]),classification_basis='basis',classification_provenance='prov',decision_origin=kw.pop('decision_origin','OPERATOR_OR_FIDUCIARY'),actor='a',actor_capacity='Trustee',**kw)
def claim(scope,issue='I1'): return p09.create_claim(**scope,issue_id=issue,proposition='claim',created_by='a')
def relationship(scope,cid,clm=None,**kw): return p09.record_authority_relationship(**scope,issue_id=kw.pop('issue_id','I1'),claim_id=clm,source_reference_id=kw.pop('source_reference_id','S1'),classification_id=cid,relationship_state=kw.pop('relationship_state','UNRESOLVED'),relationship_basis='basis',relationship_provenance='prov',decision_origin=kw.pop('decision_origin','OPERATOR_OR_FIDUCIARY'),actor='a',actor_capacity='Trustee',**kw)
def evidence(scope,clm,source='S1',**kw): return p09.add_claim_evidence(**scope,claim_id=clm,source_reference_id=source,relationship_type=kw.pop('relationship_type','DIRECT_SUPPORT'),presentation_type=kw.pop('presentation_type','SUMMARY'),evidence_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee',**kw)

def test_exact_locked_vocabularies():
 assert p09.SOURCE_TIERS == ('TIER_1_GOVERNING_AUTHORITY','TIER_2_HIGH_AUTHORITY_LEGAL_INTERPRETATION','TIER_3_PROFESSIONAL_EDUCATIONAL_SECONDARY_MATERIAL','TIER_4_CLAIMS_REQUIRING_INDEPENDENT_VERIFICATION')
 assert p09.RELATIONSHIP_STATES == ('CONTROLLING','PERSUASIVE','SUPERSEDED','NOT_APPLICABLE','UNRESOLVED')
 assert p09.SCOPE_MODIFIERS == ('FULL','PARTIAL','CONCURRENT')
 assert p09.EVIDENCE_RELATIONSHIPS == ('DIRECT_SUPPORT','PARTIAL_SUPPORT','CONTRADICTS','QUALIFIES','CONTEXT_ONLY','DOES_NOT_SUPPORT','UNRESOLVED')
 assert p09.PRESENTATION_TYPES == ('DIRECT_QUOTATION','PARAPHRASE','SUMMARY','REFERENCE_ONLY')
 assert p09.VERIFICATION_DIMENSIONS == ('SOURCE_IDENTITY_VERIFIED','SOURCE_TEXT_VERIFIED','CITATION_VERIFIED','AUTHORITY_CLASSIFICATION_VERIFIED','CLAIM_SUPPORT_VERIFIED')
 assert p09.REVIEW_STATES == ('DETECTED','REVIEW_REQUIRED','UNDER_REVIEW','RESOLVED','UNRESOLVED','CLOSED_NO_CONFLICT')
 assert p09.REVIEW_LANES == ('SYSTEM_REVIEW','OPERATOR_OR_FIDUCIARY_REVIEW','PROFESSIONAL_REVIEW')
 assert p09.DETERMINATION_STATES == ('SUPPORTED','PARTIALLY_SUPPORTED','CONTRADICTED','MIXED','INSUFFICIENT_EVIDENCE','UNRESOLVED')

def test_all_literal_source_tiers_accepted_and_invalid_rejected(env):
 _,s=env
 prior=None
 for tier in ('TIER_1_GOVERNING_AUTHORITY','TIER_2_HIGH_AUTHORITY_LEGAL_INTERPRETATION','TIER_3_PROFESSIONAL_EDUCATIONAL_SECONDARY_MATERIAL','TIER_4_CLAIMS_REQUIRING_INDEPENDENT_VERIFICATION'):
  prior=classify(s,authority_tier=tier,prior_classification_id=prior)
 with pytest.raises(ValueError,match='invalid_authority_tier'): classify(s,source_reference_id='S3',authority_tier='TIER_5_UNKNOWN')

def test_schema_separates_global_classification_and_is_append_only(env):
 path,scope=env; cid=classify(scope); c=sqlite3.connect(path); cols={r[1] for r in c.execute('pragma table_info(hub_program_authority_classifications)')}; assert not {'issue_id','claim_id','relationship_state','scope_modifier','human_confirmed'}&cols
 with pytest.raises(sqlite3.IntegrityError): c.execute('update hub_program_authority_classifications set authority_tier=authority_tier')
 c.rollback(); c.close()
 with pytest.raises(ValueError,match='prior_classification_required'): classify(scope)
 cid2=classify(scope,prior_classification_id=cid); assert cid2!=cid

def test_relationship_governance_and_context(env):
 _,s=env; cid=classify(s); clm=claim(s); relationship(s,cid); relationship(s,cid,clm)
 with pytest.raises(ValueError,match='claim_issue'): relationship(s,cid,clm,issue_id='I2')
 with pytest.raises(ValueError,match='human_confirmation'): relationship(s,cid,relationship_state='CONTROLLING')
 with pytest.raises(ValueError,match='human_confirmation'): relationship(s,cid,relationship_state='CONTROLLING',human_confirmed=True,decision_origin='SYSTEM_SUGGESTED')
 with pytest.raises(ValueError,match='express_evidence'): relationship(s,cid,relationship_state='SUPERSEDED')
 with pytest.raises(ValueError,match='objective_scope'): relationship(s,cid,relationship_state='NOT_APPLICABLE')

def test_relationship_success_cases_mismatch_and_append_only_history(env):
 path,s=env; cid=classify(s); clm=claim(s)
 controlling=relationship(s,cid,clm,relationship_state='CONTROLLING',human_confirmed=True)
 relationship(s,cid,clm,relationship_state='SUPERSEDED',express_evidence='later authority',prior_relationship_id=controlling)
 relationship(s,cid,relationship_state='NOT_APPLICABLE',objective_scope_evidence='outside jurisdiction')
 for modifier in ('FULL','PARTIAL','CONCURRENT'): relationship(s,cid,scope_modifier=modifier)
 other_cid=classify(s,source_reference_id='S2')
 with pytest.raises(ValueError,match='classification_source_mismatch'): relationship(s,other_cid,clm)
 c=sqlite3.connect(path)
 with pytest.raises(sqlite3.IntegrityError): c.execute('update hub_program_authority_relationships set relationship_basis=relationship_basis where relationship_id=?',(controlling,))
 c.rollback(); c.close()

def test_claim_requires_canonical_issue(env):
 _,s=env
 with pytest.raises(ValueError,match='issue_required'): claim(s,'')
 with pytest.raises(ValueError,match='issue_not_available'): claim(s,'IX')

def test_exact_evidence_vocabulary_and_presentation(env):
 path,s=env; clm=claim(s)
 for rel in p09.EVIDENCE_RELATIONSHIPS: evidence(s,clm,relationship_type=rel)
 for typ in p09.PRESENTATION_TYPES: evidence(s,clm,presentation_type=typ)
 for old in ('SUPPORTS','CONTEXTUALIZES','NO_SUPPORT'):
  with pytest.raises(ValueError,match='invalid_evidence'): evidence(s,clm,relationship_type=old)
 with pytest.raises(ValueError,match='presentation'): evidence(s,clm,presentation_type=None)
 eid=evidence(s,clm,source_locator=None); c=sqlite3.connect(path); assert c.execute('select source_locator from hub_program_authority_evidence where evidence_id=?',(eid,)).fetchone()[0] is None; c.close()

def test_evidence_many_to_many_and_append_only(env):
 path,s=env; first=claim(s); second=claim(s)
 ids={evidence(s,first,'S1'),evidence(s,first,'S2'),evidence(s,second,'S1')}
 assert len(ids)==3
 c=sqlite3.connect(path); assert c.execute('select count(distinct claim_id),count(distinct source_reference_id) from hub_program_authority_evidence').fetchone()==(2,2)
 with pytest.raises(sqlite3.IntegrityError): c.execute('update hub_program_authority_evidence set evidence_basis=evidence_basis')
 c.rollback(); c.close()

def verify(s,**kw):
 data=dict(dimension='SOURCE_IDENTITY_VERIFIED',result_state='SOURCE_IDENTITY_VERIFIED',verification_basis='basis',provenance='prov',decision_origin='OPERATOR_OR_FIDUCIARY',finalized=True,actor='a',actor_capacity='Trustee',source_reference_id='S1'); data.update(kw); return p09.record_verification(**s,**data)

def test_verification_compatibility_context_and_machine_rules(env):
 _,s=env
 for dim,states in p09.VERIFICATION_COMPATIBILITY.items():
  incompatible=next(x for x in p09.VERIFICATION_STATES if x not in states)
  with pytest.raises(ValueError,match='incompatible'): verify(s,dimension=dim,result_state=incompatible)
 with pytest.raises(ValueError,match='source_context'): verify(s,source_reference_id=None)
 with pytest.raises(ValueError,match='direct_source'): verify(s,dimension='SOURCE_TEXT_VERIFIED',result_state='SOURCE_TEXT_VERIFIED',decision_origin='SYSTEM_SUGGESTED')
 cid=classify(s)
 with pytest.raises(ValueError,match='objective_evidence'): verify(s,dimension='AUTHORITY_CLASSIFICATION_VERIFIED',result_state='AUTHORITY_CLASSIFICATION_VERIFIED',classification_id=cid,decision_origin='SYSTEM_SUGGESTED')
 clm=claim(s); ev=evidence(s,clm)
 with pytest.raises(ValueError,match='machine_claim'): verify(s,dimension='CLAIM_SUPPORT_VERIFIED',result_state='CLAIM_SUPPORT_VERIFIED',claim_id=clm,evidence_id=ev,decision_origin='SYSTEM_SUGGESTED')

def test_verification_matching_professional_and_negative_retention(env):
 path,s=env; cid=classify(s); other_cid=classify(s,source_reference_id='S2'); clm=claim(s); other=claim(s); ev=evidence(s,clm); other_ev=evidence(s,other)
 with pytest.raises(ValueError,match='classification_source_mismatch'): verify(s,dimension='AUTHORITY_CLASSIFICATION_VERIFIED',result_state='AUTHORITY_CLASSIFICATION_VERIFIED',classification_id=other_cid)
 with pytest.raises(ValueError,match='evidence_claim_relationship_mismatch'): verify(s,dimension='CLAIM_SUPPORT_VERIFIED',result_state='CLAIM_SUPPORT_VERIFIED',claim_id=clm,evidence_id=other_ev)
 with pytest.raises(ValueError,match='evidence_source_mismatch'): verify(s,dimension='CLAIM_SUPPORT_VERIFIED',result_state='CLAIM_SUPPORT_VERIFIED',claim_id=clm,evidence_id=ev,source_reference_id='S2')
 with pytest.raises(ValueError,match='professional_authority_required'): verify(s,classification_id=cid,decision_origin='PROFESSIONAL')
 negative=verify(s,result_state='SOURCE_IDENTITY_NOT_VERIFIED')
 c=sqlite3.connect(path); assert c.execute('select result_state,finalized from hub_program_authority_verifications where verification_id=?',(negative,)).fetchone()==('SOURCE_IDENTITY_NOT_VERIFIED',1); c.close()

def test_review_integrity_tier1_and_machine_closure(env):
 path,s=env; cid=classify(s); clm=claim(s); ev=evidence(s,clm); rel=relationship(s,cid,clm)
 rid=p09.record_review(**s,claim_id=clm,evidence_id=ev,authority_relationship_id=rel,supporting_source_reference_id='S1',review_state='DETECTED',review_lane='SYSTEM_REVIEW',resolution_basis='basis',provenance='prov',actor='system',actor_capacity='system',machine_generated=True)
 c=sqlite3.connect(path); assert c.execute('select review_state from hub_program_authority_reviews where review_id=?',(rid,)).fetchone()[0]=='REVIEW_REQUIRED'; c.close()
 with pytest.raises(ValueError,match='machine_closure'): p09.record_review(**s,claim_id=clm,evidence_id=ev,authority_relationship_id=rel,supporting_source_reference_id='S1',review_state='RESOLVED',review_lane='SYSTEM_REVIEW',resolution_basis='basis',provenance='prov',actor='system',actor_capacity='system',machine_generated=True)

def test_review_cross_claim_professional_identity_and_reopening(env):
 path,s=env; cid=classify(s); clm=claim(s); other=claim(s); ev=evidence(s,clm); other_ev=evidence(s,other); rel=relationship(s,cid,clm)
 base=dict(**s,claim_id=clm,supporting_source_reference_id='S1',review_state='UNDER_REVIEW',review_lane='OPERATOR_OR_FIDUCIARY_REVIEW',resolution_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee')
 with pytest.raises(ValueError,match='evidence_claim_relationship_mismatch'): p09.record_review(**base,evidence_id=other_ev)
 with pytest.raises(ValueError,match='professional_authority_required'): p09.record_review(**{**base,'review_lane':'PROFESSIONAL_REVIEW'})
 professional=p09.record_review(**{**base,'review_lane':'PROFESSIONAL_REVIEW','professional_authority':'Bar admission','actor_capacity':'Attorney'},evidence_id=ev,authority_relationship_id=rel)
 reopened=p09.reopen_review(**{**base,'prior_review_id':professional},evidence_id=ev,authority_relationship_id=rel)
 c=sqlite3.connect(path); assert c.execute('select prior_review_id,review_state from hub_program_authority_reviews where review_id=?',(reopened,)).fetchone()==(professional,'REVIEW_REQUIRED')
 with pytest.raises(sqlite3.IntegrityError): c.execute('update hub_program_authority_reviews set resolution_basis=resolution_basis')
 c.rollback(); c.close()

def test_determination_requires_same_claim_connected_chain(env):
 _,s=env; cid=classify(s); clm=claim(s); ev=evidence(s,clm); rel=relationship(s,cid,clm)
 did=p09.record_determination(**s,claim_id=clm,determination_state='SUPPORTED',determination_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee',backtrace=[ev,cid,rel]); assert did.startswith('DET-')
 other=claim(s); other_ev=evidence(s,other)
 with pytest.raises(ValueError,match='backtrace'): p09.record_determination(**s,claim_id=clm,determination_state='SUPPORTED',determination_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee',backtrace=[other_ev,cid,rel])
 with pytest.raises(ValueError,match='evidence_required'): p09.record_determination(**s,claim_id=clm,determination_state='SUPPORTED',determination_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee',backtrace=[cid,rel])
 with pytest.raises(ValueError,match='invalid_determination_state'): p09.record_determination(**s,claim_id=clm,determination_state='TRUE',determination_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee',backtrace=[ev,cid,rel])

def determine(s,clm,backtrace,state='SUPPORTED'):
 return p09.record_determination(**s,claim_id=clm,determination_state=state,determination_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee',backtrace=backtrace)

def test_determination_validates_every_node_in_order_independent_graph(env):
 path,s=env; clm=claim(s); ev=evidence(s,clm); cid=classify(s); rel=relationship(s,cid,clm)
 first=determine(s,clm,[f'REL:{rel}',f'EVD:{ev}',f'CLS:{cid}'])
 disconnected_cls=classify(s,source_reference_id='S2')
 disconnected_rel=relationship(s,disconnected_cls,clm,source_reference_id='S2')
 for trace in ([ev,cid,rel,disconnected_cls], [ev,cid,rel,disconnected_rel], [ev,cid,disconnected_rel], [ev,cid,rel,'BOGUS-X'], [f'BOGUS:{ev}',cid,rel]):
  with pytest.raises(ValueError,match='backtrace'): determine(s,clm,trace)
 other=claim(s); other_rel=relationship(s,cid,other)
 with pytest.raises(ValueError,match='backtrace'): determine(s,clm,[ev,cid,rel,other_rel])
 with pytest.raises(ValueError,match='relationship_required'): determine(s,clm,[ev,cid])
 second=determine(s,clm,[ev,cid,rel,first])
 assert second!=first
 c=sqlite3.connect(path)
 assert c.execute('select count(*) from hub_program_authority_determinations').fetchone()[0]==2
 with pytest.raises(sqlite3.IntegrityError): c.execute('update hub_program_authority_determinations set determination_basis=determination_basis where determination_id=?',(first,))
 c.rollback(); c.close()
 for invalid_state in ('TRUE','FALSE','LEGALLY_VALID'):
  with pytest.raises(ValueError,match='invalid_determination_state'): determine(s,clm,[ev,cid,rel],invalid_state)
 other_ev=evidence(s,other); other_det=determine(s,other,[other_ev,cid,other_rel])
 with pytest.raises(ValueError,match='backtrace'): determine(s,clm,[ev,cid,rel,other_det])

def test_determination_rejects_disconnected_verification_and_review_nodes(env):
 path,s=env; clm=claim(s); ev=evidence(s,clm); cid=classify(s); rel=relationship(s,cid,clm)
 disconnected_cls=classify(s,source_reference_id='S2')
 disconnected_ver=verify(s,claim_id=clm,source_reference_id='S2')
 authority_ver=verify(s,dimension='AUTHORITY_CLASSIFICATION_VERIFIED',result_state='AUTHORITY_CLASSIFICATION_VERIFIED',source_reference_id='S2',classification_id=disconnected_cls)
 other=claim(s); other_ev=evidence(s,other); other_claim_ver=verify(s,dimension='CLAIM_SUPPORT_VERIFIED',result_state='CLAIM_SUPPORT_VERIFIED',claim_id=other,evidence_id=other_ev,source_reference_id='S1')
 disconnected_review=p09.record_review(**s,claim_id=clm,supporting_source_reference_id='S2',review_state='UNRESOLVED',review_lane='OPERATOR_OR_FIDUCIARY_REVIEW',resolution_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee')
 for node in (disconnected_ver,authority_ver,other_claim_ver,disconnected_review):
  with pytest.raises(ValueError,match='backtrace'): determine(s,clm,[ev,cid,rel,node])
 valid_ver=verify(s,claim_id=clm,source_reference_id='S1')
 valid_review=p09.record_review(**s,claim_id=clm,evidence_id=ev,authority_relationship_id=rel,supporting_source_reference_id='S1',review_state='UNRESOLVED',review_lane='OPERATOR_OR_FIDUCIARY_REVIEW',resolution_basis='basis',provenance='prov',actor='a',actor_capacity='Trustee')
 assert determine(s,clm,[valid_review,rel,valid_ver,cid,ev]).startswith('DET-')
 c=sqlite3.connect(path)
 c.execute("INSERT INTO hub_program_authority_reviews VALUES('REVW-HIDDEN','P1',?,?,NULL,?,'UNRESOLVED','OPERATOR_OR_FIDUCIARY_REVIEW','basis','prov','S1','a','Trustee',NULL,0,'now')",(clm,ev,rel)); c.commit(); c.close()
 with pytest.raises(ValueError,match='backtrace'): determine(s,clm,[ev,cid,'REVW-HIDDEN',rel.replace('REL-','REL-MISSING-')])

def test_migration_idempotent_empty_no_permissions(env):
 path,_=env; apply_work_learning_authority_schema(path); c=sqlite3.connect(path); assert all(c.execute(f'select count(*) from {t}').fetchone()[0]==0 for t in TABLES); c.close()

def test_route_role_scope_and_human_origin_contract():
 app_source=Path('app.py').read_text(encoding='utf-8')
 assert '"workspace_program_authority": {"Admin", "Trustee", "Viewer"}' in app_source
 assert '"workspace_program_authority_mutate": {"Admin", "Trustee"}' in app_source
 start=app_source.index('def workspace_program_authority_mutate')
 end=app_source.index('\n\n@app.route(',start)
 route=app_source[start:end]
 assert 'validate_csrf_token()' in route
 assert 'set(request.form) - fields[action]' in route
 assert 'firm_id' not in route[route.index('fields = {'):route.index('actor = ')]
 assert 'owner_id' not in route[route.index('fields = {'):route.index('actor = ')]
 assert 'decision_origin="OPERATOR_OR_FIDUCIARY"' in route
 assert 'machine_generated=False' in route
 assert '_workspace_program_context(workspace_id, program_id)' in route
