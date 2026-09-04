"""P09 append-only authority, evidence, verification, review service."""
import json, sqlite3, uuid
from datetime import datetime, timezone
from database.db import get_connection
from services.services_work_learning_programs import get_hub_program

SOURCE_TIERS=('TIER_1_GOVERNING_AUTHORITY','TIER_2_HIGH_AUTHORITY_LEGAL_INTERPRETATION','TIER_3_PROFESSIONAL_EDUCATIONAL_SECONDARY_MATERIAL','TIER_4_CLAIMS_REQUIRING_INDEPENDENT_VERIFICATION')
RELATIONSHIP_STATES=('CONTROLLING','PERSUASIVE','SUPERSEDED','NOT_APPLICABLE','UNRESOLVED')
SCOPE_MODIFIERS=('FULL','PARTIAL','CONCURRENT'); DECISION_ORIGINS=('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')
EVIDENCE_RELATIONSHIPS=('DIRECT_SUPPORT','PARTIAL_SUPPORT','CONTRADICTS','QUALIFIES','CONTEXT_ONLY','DOES_NOT_SUPPORT','UNRESOLVED')
PRESENTATION_TYPES=('DIRECT_QUOTATION','PARAPHRASE','SUMMARY','REFERENCE_ONLY')
VERIFICATION_DIMENSIONS=('SOURCE_IDENTITY_VERIFIED','SOURCE_TEXT_VERIFIED','CITATION_VERIFIED','AUTHORITY_CLASSIFICATION_VERIFIED','CLAIM_SUPPORT_VERIFIED')
VERIFICATION_COMPATIBILITY={'SOURCE_IDENTITY_VERIFIED':('SOURCE_IDENTITY_VERIFIED','SOURCE_IDENTITY_NOT_VERIFIED','INSUFFICIENT_EVIDENCE'),'SOURCE_TEXT_VERIFIED':('SOURCE_TEXT_VERIFIED','SOURCE_TEXT_MISMATCH','INSUFFICIENT_EVIDENCE'),'CITATION_VERIFIED':('CITATION_VERIFIED','CITATION_MISMATCH','INSUFFICIENT_EVIDENCE'),'AUTHORITY_CLASSIFICATION_VERIFIED':('AUTHORITY_CLASSIFICATION_VERIFIED','AUTHORITY_CLASSIFICATION_DISPUTED','INSUFFICIENT_EVIDENCE'),'CLAIM_SUPPORT_VERIFIED':('CLAIM_SUPPORT_VERIFIED','CLAIM_NOT_SUPPORTED','INSUFFICIENT_EVIDENCE')}
VERIFICATION_STATES=tuple(dict.fromkeys(x for values in VERIFICATION_COMPATIBILITY.values() for x in values))
REVIEW_STATES=('DETECTED','REVIEW_REQUIRED','UNDER_REVIEW','RESOLVED','UNRESOLVED','CLOSED_NO_CONFLICT'); REVIEW_LANES=('SYSTEM_REVIEW','OPERATOR_OR_FIDUCIARY_REVIEW','PROFESSIONAL_REVIEW')
DETERMINATION_STATES=('SUPPORTED','PARTIALLY_SUPPORTED','CONTRADICTED','MIXED','INSUFFICIENT_EVIDENCE','UNRESOLVED')

def _id(p): return p+'-'+uuid.uuid4().hex[:10].upper()
def _now(): return datetime.now(timezone.utc).isoformat()
def _required(v,code):
 v=(v or '').strip()
 if not v: raise ValueError(code)
 return v
def _one(sql,args):
 c=get_connection(); c.row_factory=sqlite3.Row; r=c.execute(sql,args).fetchone(); c.close(); return dict(r) if r else None
def _insert(table,columns,values):
 c=get_connection(); c.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in values)})",values); c.commit(); c.close()
def _scope(*,program_id,workspace_id,firm_id,owner_id):
 p=get_hub_program(program_id=program_id,firm_id=firm_id,owner_id=owner_id)
 if not p or p['workspace_id']!=workspace_id: raise ValueError('program_not_available_in_context')
 return p
def _issue(program_id,issue_id):
 issue_id=_required(issue_id,'issue_required'); r=_one('SELECT issue_id,program_id FROM hub_program_issues WHERE issue_id=? AND program_id=?',(issue_id,program_id))
 if not r: raise ValueError('issue_not_available_in_context')
 return r
def _source(program_id,source_id,issue_id=None):
 r=_one('SELECT source_reference_id,program_id,issue_id FROM hub_program_source_references WHERE source_reference_id=? AND program_id=?',(source_id,program_id))
 if not r: raise ValueError('source_not_available_in_context')
 if issue_id and r.get('issue_id') and r['issue_id']!=issue_id: raise ValueError('source_issue_relationship_mismatch')
 return r
def _claim(program_id,claim_id):
 r=_one('SELECT * FROM hub_program_authority_claims WHERE claim_id=? AND program_id=?',(claim_id,program_id))
 if not r: raise ValueError('claim_not_available_in_context')
 return r

def classify_source_authority(*,program_id,workspace_id,firm_id,owner_id,source_reference_id,authority_tier,classification_basis,classification_provenance,decision_origin,actor,actor_capacity,prior_classification_id=None,professional_authority=None):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); _source(program_id,source_reference_id)
 if authority_tier not in SOURCE_TIERS: raise ValueError('invalid_authority_tier')
 if decision_origin not in DECISION_ORIGINS: raise ValueError('invalid_decision_origin')
 if decision_origin=='PROFESSIONAL' and (not (professional_authority or '').strip() or not (actor_capacity or '').strip()): raise ValueError('professional_authority_required')
 latest=_one('SELECT * FROM hub_program_authority_classifications WHERE program_id=? AND source_reference_id=? ORDER BY created_at DESC,classification_id DESC LIMIT 1',(program_id,source_reference_id))
 if latest and prior_classification_id!=latest['classification_id']: raise ValueError('prior_classification_required')
 if not latest and prior_classification_id: raise ValueError('prior_classification_not_available_in_context')
 cid=_id('CLS'); _insert('hub_program_authority_classifications',('classification_id','program_id','source_reference_id','authority_tier','classification_basis','classification_provenance','decision_origin','professional_authority','actor','actor_capacity','prior_classification_id','created_at'),(cid,program_id,source_reference_id,authority_tier,_required(classification_basis,'classification_basis_required'),_required(classification_provenance,'classification_provenance_required'),decision_origin,(professional_authority or '').strip() or None,_required(actor,'actor_required'),_required(actor_capacity,'actor_capacity_required'),prior_classification_id,_now())); return cid

def record_authority_relationship(*,program_id,workspace_id,firm_id,owner_id,issue_id,source_reference_id,classification_id,relationship_state,relationship_basis,relationship_provenance,decision_origin,actor,actor_capacity,claim_id=None,scope_modifier=None,human_confirmed=False,professional_authority=None,express_evidence=None,objective_scope_evidence=None,prior_relationship_id=None):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); _issue(program_id,issue_id); _source(program_id,source_reference_id,issue_id)
 classification=_one('SELECT * FROM hub_program_authority_classifications WHERE classification_id=? AND program_id=?',(classification_id,program_id))
 if not classification or classification['source_reference_id']!=source_reference_id: raise ValueError('classification_source_mismatch')
 if claim_id and _claim(program_id,claim_id)['issue_id']!=issue_id: raise ValueError('claim_issue_relationship_mismatch')
 if relationship_state not in RELATIONSHIP_STATES: raise ValueError('invalid_relationship_state')
 if scope_modifier and scope_modifier not in SCOPE_MODIFIERS: raise ValueError('invalid_scope_modifier')
 if decision_origin not in DECISION_ORIGINS: raise ValueError('invalid_decision_origin')
 if relationship_state=='CONTROLLING' and (not human_confirmed or decision_origin=='SYSTEM_SUGGESTED'): raise ValueError('controlling_requires_human_confirmation')
 if relationship_state=='SUPERSEDED': _required(express_evidence,'superseded_requires_express_evidence')
 if relationship_state=='NOT_APPLICABLE': _required(objective_scope_evidence,'not_applicable_requires_objective_scope_evidence')
 if decision_origin=='PROFESSIONAL' and (not (professional_authority or '').strip() or not (actor_capacity or '').strip()): raise ValueError('professional_authority_required')
 if prior_relationship_id:
  prior=_one('SELECT * FROM hub_program_authority_relationships WHERE relationship_id=? AND program_id=?',(prior_relationship_id,program_id))
  if not prior or prior['issue_id']!=issue_id or prior['claim_id']!=(claim_id or None) or prior['source_reference_id']!=source_reference_id: raise ValueError('prior_relationship_not_available_in_context')
 rid=_id('REL'); _insert('hub_program_authority_relationships',('relationship_id','program_id','issue_id','claim_id','source_reference_id','classification_id','relationship_state','scope_modifier','relationship_basis','relationship_provenance','decision_origin','human_confirmed','professional_authority','express_evidence','objective_scope_evidence','prior_relationship_id','actor','actor_capacity','created_at'),(rid,program_id,issue_id,claim_id or None,source_reference_id,classification_id,relationship_state,scope_modifier,_required(relationship_basis,'relationship_basis_required'),_required(relationship_provenance,'relationship_provenance_required'),decision_origin,int(bool(human_confirmed)),(professional_authority or '').strip() or None,(express_evidence or '').strip() or None,(objective_scope_evidence or '').strip() or None,prior_relationship_id,_required(actor,'actor_required'),_required(actor_capacity,'actor_capacity_required'),_now())); return rid

def create_claim(*,program_id,workspace_id,firm_id,owner_id,issue_id,proposition,created_by):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); _issue(program_id,issue_id); cid=_id('CLM'); _insert('hub_program_authority_claims',('claim_id','program_id','issue_id','proposition','created_by','created_at'),(cid,program_id,issue_id,_required(proposition,'claim_proposition_required'),_required(created_by,'actor_required'),_now())); return cid

def add_claim_evidence(*,program_id,workspace_id,firm_id,owner_id,claim_id,source_reference_id,relationship_type,presentation_type,evidence_basis,provenance,actor,actor_capacity,source_locator=None):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); claim=_claim(program_id,claim_id); _source(program_id,source_reference_id,claim['issue_id'])
 if relationship_type not in EVIDENCE_RELATIONSHIPS: raise ValueError('invalid_evidence_relationship')
 if presentation_type not in PRESENTATION_TYPES: raise ValueError('invalid_presentation_type')
 eid=_id('EVD'); _insert('hub_program_authority_evidence',('evidence_id','program_id','claim_id','source_reference_id','relationship_type','presentation_type','source_locator','evidence_basis','provenance','actor','actor_capacity','created_at'),(eid,program_id,claim_id,source_reference_id,relationship_type,presentation_type,(source_locator or '').strip() or None,_required(evidence_basis,'evidence_basis_required'),_required(provenance,'provenance_required'),_required(actor,'actor_required'),_required(actor_capacity,'actor_capacity_required'),_now())); return eid

def record_verification(*,program_id,workspace_id,firm_id,owner_id,dimension,result_state,verification_basis,provenance,decision_origin,finalized,actor,actor_capacity,claim_id=None,evidence_id=None,source_reference_id=None,classification_id=None,direct_source_comparison=None,objective_evidence=None,professional_authority=None):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id)
 if dimension not in VERIFICATION_DIMENSIONS: raise ValueError('invalid_verification_dimension')
 if result_state not in VERIFICATION_COMPATIBILITY[dimension]: raise ValueError('incompatible_verification_result')
 if decision_origin not in DECISION_ORIGINS: raise ValueError('invalid_decision_origin')
 claim=_claim(program_id,claim_id) if claim_id else None; evidence=_one('SELECT * FROM hub_program_authority_evidence WHERE evidence_id=? AND program_id=?',(evidence_id,program_id)) if evidence_id else None
 if evidence_id and not evidence: raise ValueError('evidence_not_available_in_context')
 if dimension in ('SOURCE_IDENTITY_VERIFIED','SOURCE_TEXT_VERIFIED','CITATION_VERIFIED'):
  if not source_reference_id: raise ValueError('source_context_required')
  _source(program_id,source_reference_id)
 if dimension=='AUTHORITY_CLASSIFICATION_VERIFIED':
  if not source_reference_id or not classification_id: raise ValueError('classification_context_required')
  _source(program_id,source_reference_id); cls=_one('SELECT * FROM hub_program_authority_classifications WHERE classification_id=? AND program_id=?',(classification_id,program_id))
  if not cls or cls['source_reference_id']!=source_reference_id: raise ValueError('classification_source_mismatch')
 if dimension=='CLAIM_SUPPORT_VERIFIED':
  if not claim or not evidence: raise ValueError('claim_evidence_context_required')
  if evidence['claim_id']!=claim_id: raise ValueError('evidence_claim_relationship_mismatch')
  if source_reference_id and source_reference_id!=evidence['source_reference_id']: raise ValueError('evidence_source_mismatch')
  source_reference_id=evidence['source_reference_id']
 if classification_id:
  cls=_one('SELECT * FROM hub_program_authority_classifications WHERE classification_id=? AND program_id=?',(classification_id,program_id))
  if not cls or cls['source_reference_id']!=source_reference_id: raise ValueError('classification_source_mismatch')
 if decision_origin=='PROFESSIONAL' and (not (professional_authority or '').strip() or not (actor_capacity or '').strip()): raise ValueError('professional_authority_required')
 if decision_origin=='SYSTEM_SUGGESTED' and finalized:
  if dimension=='CLAIM_SUPPORT_VERIFIED': raise ValueError('machine_claim_support_finalization_prohibited')
  if dimension in ('SOURCE_TEXT_VERIFIED','CITATION_VERIFIED') and not (direct_source_comparison or '').strip(): raise ValueError('direct_source_comparison_required')
  if dimension in ('SOURCE_IDENTITY_VERIFIED','AUTHORITY_CLASSIFICATION_VERIFIED') and not (objective_evidence or '').strip(): raise ValueError('objective_evidence_required')
 vid=_id('VER'); cols=('verification_id','program_id','claim_id','evidence_id','source_reference_id','classification_id','dimension','result_state','verification_basis','provenance','decision_origin','finalized','direct_source_comparison','objective_evidence','professional_authority','actor','actor_capacity','created_at'); vals=(vid,program_id,claim_id,evidence_id,source_reference_id,classification_id,dimension,result_state,_required(verification_basis,'verification_basis_required'),_required(provenance,'provenance_required'),decision_origin,int(bool(finalized)),(direct_source_comparison or '').strip() or None,(objective_evidence or '').strip() or None,(professional_authority or '').strip() or None,_required(actor,'actor_required'),_required(actor_capacity,'actor_capacity_required'),_now()); _insert('hub_program_authority_verifications',cols,vals); return vid

def record_review(*,program_id,workspace_id,firm_id,owner_id,claim_id,supporting_source_reference_id,review_state,review_lane,resolution_basis,provenance,actor,actor_capacity,evidence_id=None,prior_review_id=None,authority_relationship_id=None,professional_authority=None,machine_generated=False):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); claim=_claim(program_id,claim_id); _source(program_id,supporting_source_reference_id,claim['issue_id'])
 evidence=_one('SELECT * FROM hub_program_authority_evidence WHERE evidence_id=? AND program_id=?',(evidence_id,program_id)) if evidence_id else None
 if evidence_id and (not evidence or evidence['claim_id']!=claim_id or evidence['source_reference_id']!=supporting_source_reference_id): raise ValueError('evidence_claim_relationship_mismatch')
 if prior_review_id:
  prior=_one('SELECT * FROM hub_program_authority_reviews WHERE review_id=? AND program_id=?',(prior_review_id,program_id))
  if not prior or prior['claim_id']!=claim_id: raise ValueError('prior_review_claim_mismatch')
 relationship=None
 if authority_relationship_id:
  relationship=_one('SELECT * FROM hub_program_authority_relationships WHERE relationship_id=? AND program_id=?',(authority_relationship_id,program_id))
  if not relationship or relationship['source_reference_id']!=supporting_source_reference_id or relationship['issue_id']!=claim['issue_id'] or relationship['claim_id'] not in (None,claim_id): raise ValueError('authority_relationship_context_mismatch')
 if review_state not in REVIEW_STATES or review_lane not in REVIEW_LANES: raise ValueError('invalid_review')
 if review_lane=='PROFESSIONAL_REVIEW' and (not (professional_authority or '').strip() or not (actor_capacity or '').strip()): raise ValueError('professional_authority_required')
 if machine_generated and review_state in ('RESOLVED','CLOSED_NO_CONFLICT'): raise ValueError('interpretive_machine_closure_prohibited')
 if relationship:
  cls=_one('SELECT authority_tier FROM hub_program_authority_classifications WHERE classification_id=? AND program_id=?',(relationship['classification_id'],program_id))
  if cls and cls['authority_tier']=='TIER_1_GOVERNING_AUTHORITY' and review_state=='DETECTED': review_state='REVIEW_REQUIRED'
 rid=_id('REVW'); cols=('review_id','program_id','claim_id','evidence_id','prior_review_id','authority_relationship_id','review_state','review_lane','resolution_basis','provenance','supporting_source_reference_id','actor','actor_capacity','professional_authority','machine_generated','created_at'); vals=(rid,program_id,claim_id,evidence_id,prior_review_id,authority_relationship_id,review_state,review_lane,_required(resolution_basis,'resolution_basis_required'),_required(provenance,'provenance_required'),supporting_source_reference_id,_required(actor,'actor_required'),_required(actor_capacity,'actor_capacity_required'),(professional_authority or '').strip() or None,int(bool(machine_generated)),_now()); _insert('hub_program_authority_reviews',cols,vals); return rid

def reopen_review(**kwargs):
 if not kwargs.get('prior_review_id'): raise ValueError('prior_review_required')
 kwargs['review_state']='REVIEW_REQUIRED'; return record_review(**kwargs)

def record_determination(*,program_id,workspace_id,firm_id,owner_id,claim_id,determination_state,determination_basis,provenance,actor,actor_capacity,backtrace,issue_id=None):
 _scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); claim=_claim(program_id,claim_id)
 if issue_id and issue_id!=claim['issue_id']: raise ValueError('claim_issue_relationship_mismatch')
 if determination_state not in DETERMINATION_STATES: raise ValueError('invalid_determination_state')
 if not isinstance(backtrace,(list,tuple)): raise ValueError('determination_backtrace_required')
 normalized=[]; rows={'EVD':{},'CLS':{},'REL':{},'VER':{},'REVW':{},'DET':{}}
 tables={'EVD':('hub_program_authority_evidence','evidence_id'),'CLS':('hub_program_authority_classifications','classification_id'),'REL':('hub_program_authority_relationships','relationship_id'),'VER':('hub_program_authority_verifications','verification_id'),'REVW':('hub_program_authority_reviews','review_id'),'DET':('hub_program_authority_determinations','determination_id')}
 # Resolve the complete typed graph first; validation below is order-independent.
 for raw in backtrace:
  token=str(raw).strip(); declared,separator,record_id=token.partition(':')
  if not separator: record_id=declared
  prefix=record_id.split('-',1)[0]
  if prefix not in tables or (separator and declared!=prefix): raise ValueError('invalid_determination_backtrace')
  table,key=tables[prefix]; row=_one(f'SELECT * FROM {table} WHERE {key}=? AND program_id=?',(record_id,program_id))
  if not row: raise ValueError('invalid_determination_backtrace')
  rows[prefix][record_id]=row; normalized.append(record_id)
 evidence_sources=set()
 for evidence_row in rows['EVD'].values():
  if evidence_row['claim_id']!=claim_id: raise ValueError('invalid_determination_backtrace')
  evidence_sources.add(evidence_row['source_reference_id'])
 if not evidence_sources: raise ValueError('determination_evidence_required')
 for classification in rows['CLS'].values():
  if classification['source_reference_id'] not in evidence_sources: raise ValueError('invalid_determination_backtrace')
 if not rows['CLS']: raise ValueError('determination_classification_required')
 def connected_relationship(relationship):
  classification=rows['CLS'].get(relationship['classification_id'])
  return (relationship['issue_id']==claim['issue_id'] and relationship['claim_id'] in (None,claim_id)
          and relationship['source_reference_id'] in evidence_sources and classification is not None
          and classification['source_reference_id']==relationship['source_reference_id'])
 if not rows['REL']: raise ValueError('determination_authority_relationship_required')
 if any(not connected_relationship(relationship) for relationship in rows['REL'].values()): raise ValueError('invalid_determination_backtrace')
 for verification in rows['VER'].values():
  if verification['claim_id'] is not None and verification['claim_id']!=claim_id: raise ValueError('invalid_determination_backtrace')
  source_id=verification['source_reference_id']; evidence_row=None
  if verification['evidence_id']:
   evidence_row=_one('SELECT * FROM hub_program_authority_evidence WHERE evidence_id=? AND program_id=?',(verification['evidence_id'],program_id))
   if not evidence_row or evidence_row['claim_id']!=claim_id or evidence_row['source_reference_id']!=source_id: raise ValueError('invalid_determination_backtrace')
  if verification['dimension']=='CLAIM_SUPPORT_VERIFIED':
   if verification['claim_id']!=claim_id or not evidence_row or source_id not in evidence_sources: raise ValueError('invalid_determination_backtrace')
  elif verification['dimension'] in ('SOURCE_IDENTITY_VERIFIED','SOURCE_TEXT_VERIFIED','CITATION_VERIFIED'):
   if not source_id or source_id not in evidence_sources: raise ValueError('invalid_determination_backtrace')
  elif verification['dimension']=='AUTHORITY_CLASSIFICATION_VERIFIED':
   classification=rows['CLS'].get(verification['classification_id'])
   if source_id not in evidence_sources or not classification or classification['source_reference_id']!=source_id: raise ValueError('invalid_determination_backtrace')
  else: raise ValueError('invalid_determination_backtrace')
 for review in rows['REVW'].values():
  source_id=review['supporting_source_reference_id']
  if review['claim_id']!=claim_id or source_id not in evidence_sources: raise ValueError('invalid_determination_backtrace')
  if review['evidence_id']:
   evidence_row=_one('SELECT * FROM hub_program_authority_evidence WHERE evidence_id=? AND program_id=?',(review['evidence_id'],program_id))
   if not evidence_row or evidence_row['claim_id']!=claim_id or evidence_row['source_reference_id']!=source_id: raise ValueError('invalid_determination_backtrace')
  if review['authority_relationship_id']:
   relationship=rows['REL'].get(review['authority_relationship_id'])
   if not relationship or relationship['source_reference_id']!=source_id or not connected_relationship(relationship): raise ValueError('invalid_determination_backtrace')
 for prior in rows['DET'].values():
  if prior['claim_id']!=claim_id or prior['issue_id']!=claim['issue_id']: raise ValueError('invalid_determination_backtrace')
 did=_id('DET'); _insert('hub_program_authority_determinations',('determination_id','program_id','issue_id','claim_id','determination_state','determination_basis','provenance','actor','actor_capacity','backtrace_json','created_at'),(did,program_id,claim['issue_id'],claim_id,determination_state,_required(determination_basis,'determination_basis_required'),_required(provenance,'provenance_required'),_required(actor,'actor_required'),_required(actor_capacity,'actor_capacity_required'),json.dumps(normalized),_now())); return did

def get_program_authority_read_model(*,program_id,workspace_id,firm_id,owner_id):
 program=_scope(program_id=program_id,workspace_id=workspace_id,firm_id=firm_id,owner_id=owner_id); c=get_connection(); c.row_factory=sqlite3.Row
 def rows(sql): return [dict(r) for r in c.execute(sql,(program_id,)).fetchall()]
 model={'program':program,'issues':rows('SELECT * FROM hub_program_issues WHERE program_id=? ORDER BY created_at'),'sources':rows('SELECT * FROM hub_program_source_references WHERE program_id=? ORDER BY created_at'),'classifications':rows('SELECT * FROM hub_program_authority_classifications WHERE program_id=? ORDER BY created_at'),'relationships':rows('SELECT * FROM hub_program_authority_relationships WHERE program_id=? ORDER BY created_at'),'claims':rows('SELECT * FROM hub_program_authority_claims WHERE program_id=? ORDER BY created_at'),'evidence':rows('SELECT * FROM hub_program_authority_evidence WHERE program_id=? ORDER BY created_at'),'verifications':rows('SELECT * FROM hub_program_authority_verifications WHERE program_id=? ORDER BY created_at'),'reviews':rows('SELECT * FROM hub_program_authority_reviews WHERE program_id=? ORDER BY created_at'),'determinations':rows('SELECT * FROM hub_program_authority_determinations WHERE program_id=? ORDER BY created_at')}; c.close(); return model
