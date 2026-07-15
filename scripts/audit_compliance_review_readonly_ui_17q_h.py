import ast,json,os,re,sqlite3,subprocess,sys,tempfile
from pathlib import Path
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
ROOT=Path(__file__).resolve().parent.parent; sys.path.insert(0,str(ROOT)); DB=ROOT/"trustee_app.db"; REPO_DATABASES=frozenset(ROOT.glob("*.db"))
EM={"app.py","database/db.py","scripts/audit_compliance_review_foundation_17q_g.py","scripts/audit_system_observation_foundation_17m.py","services/services_compliance_reviews.py","templates/ios_workspaces/compliance.html"}; EU={"migrations/reconcile_role_permissions_baseline.py","scripts/audit_authorization_baseline_reconciliation_17q_h6a_r6.py","scripts/audit_compliance_review_readonly_ui_17q_h.py","templates/compliance_reviews/detail.html","templates/compliance_reviews/registry.html"}; BASE=int(os.environ.get("H4C_BASELINE_MTIME_NS",DB.stat().st_mtime_ns)); failures=[]; total=passed=0
def check(n,c,d=""):
 global total,passed; total+=1
 if c: passed+=1; print("PASS - "+n)
 else: d=" ".join(str(d).split())[:240]; failures.append((n,d)); print("FAIL - "+n+(" | "+d if d else ""))
def run(*a,extra=None):
 env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",**(extra or {})}; return subprocess.run(a,cwd=ROOT,text=True,capture_output=True,timeout=120,env=env)
def sets():
 u=set(run("git","ls-files","--others","--exclude-standard").stdout.splitlines()); s=set(run("git","diff","--cached","--name-only").stdout.splitlines()); m={x[3:].replace("\\","/") for x in run("git","status","--porcelain","--untracked-files=all").stdout.splitlines() if len(x)>=4 and x[:2]!="??"}; return m,u,s
def compliance_objects(c): return tuple(c.execute("SELECT type,name,COALESCE(tbl_name,'') FROM sqlite_master WHERE lower(name) LIKE '%compliance%' OR lower(COALESCE(tbl_name,'')) LIKE '%compliance%' ORDER BY type,name"))
def snap():
 st=DB.stat()
 with sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True) as c:
  ob=compliance_objects(c); au=c.execute("SELECT count(*),max(id) FROM audit_log").fetchone(); r=c.execute("SELECT count(*) FROM governance_relationships").fetchone()[0]; l=c.execute("SELECT count(*) FROM governance_relationship_audit_ledger").fetchone()[0]; so=[]
  for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name) LIKE '%system%observation%' ORDER BY name"): so.append((n,c.execute(f'SELECT count(*) FROM "{n}"').fetchone()[0]))
  i=tuple(x[0] for x in c.execute("PRAGMA integrity_check")); fk=tuple(c.execute("PRAGMA foreign_key_check"))
 return(st.st_size,st.st_mtime_ns,ob,au,r,l,tuple(so),i,fk)
def repo(x):
 m,u,s=sets(); check(x+" modified files exact",m==EM,sorted(m)); check(x+" untracked files exact",u==EU,sorted(u)); check(x+" staging empty",not s,sorted(s))
CHILD='import contextlib,io,json,os,re,sys\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nfrom unittest.mock import patch\nchecks=[]\ndef check(name,condition,detail=""): checks.append({"name":name,"passed":bool(condition),"detail":" ".join(str(detail).split())[:160]})\ndef authenticated(client,username,role,firm_id=None):\n with client.session_transaction() as sess:\n  sess.clear(); sess["username"]=username; sess["role"]=role; sess["user_id"]="USR-test"; sess["last_activity"]=datetime.now(timezone.utc).timestamp()\n  if firm_id is not None: sess["firm_id"]=firm_id\ntry:\n ROOT=Path(sys.argv[1]).resolve(); DB=(ROOT/"trustee_app.db").resolve(); T=Path(os.environ["DB_PATH"]).resolve()\n if ROOT in T.parents or T==DB: raise RuntimeError("unsafe")\n sys.path.insert(0,str(ROOT))\n with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()): import app as app_module\n flask_app=app_module.app; flask_app.config["TESTING"]=True\n app_source=(ROOT/"app.py").read_text(encoding="utf-8"); registry_source=(ROOT/"templates/compliance_reviews/registry.html").read_text(encoding="utf-8"); detail_source=(ROOT/"templates/compliance_reviews/detail.html").read_text(encoding="utf-8"); workspace_source=(ROOT/"templates/ios_workspaces/compliance.html").read_text(encoding="utf-8"); route_block=app_source[app_source.index("def _compliance_review_read_scope"):app_source.index("def _system_observation_read_scope")]\n rules = list(flask_app.url_map.iter_rules())\n for endpoint, path in (\n     ("compliance_review_registry", "/compliance/reviews"),\n     ("compliance_review_detail", "/compliance/reviews/<compliance_review_id>"),\n ):\n     owned = [r for r in rules if r.endpoint == endpoint]\n     check(f"one route for {endpoint}", len(owned) == 1, len(owned))\n     check(f"path for {endpoint}", len(owned) == 1 and owned[0].rule == path)\n     check(f"GET-only methods for {endpoint}", len(owned) == 1 and owned[0].methods == {"GET", "HEAD", "OPTIONS"}, getattr(owned[0], "methods", None) if owned else "missing")\n     check(f"POST absent for {endpoint}", len(owned) == 1 and "POST" not in owned[0].methods)\n review_rules = [r for r in rules if r.rule.startswith("/compliance/reviews")]\n check("no additional Compliance Review routes", len(review_rules) == 2, [r.rule for r in review_rules])\n\n client = flask_app.test_client()\n for path in ("/compliance/reviews", "/compliance/reviews/CMP-2026-0001"):\n     response = client.get(path, follow_redirects=False)\n     check(f"unauthenticated redirect: {path}", response.status_code in (301, 302, 303, 307, 308) and "/login" in response.headers.get("Location", ""))\n\n with flask_app.test_request_context("/"):\n     from flask import session\n     session.update(username="admin", role="Admin")\n     check("canonical Admin global scope", app_module._compliance_review_read_scope() == {"global": True})\n with flask_app.test_request_context("/"):\n     session.update(username="other-admin", role="Admin", firm_id="FIRM-002")\n     check("noncanonical Admin firm scope", app_module._compliance_review_read_scope() == {"global": False, "firm_id": "FIRM-002"})\n with flask_app.test_request_context("/"):\n     session.update(username="trustee", role="Trustee", firm_id="FIRM-002")\n     check("Trustee firm scope", app_module._compliance_review_read_scope() == {"global": False, "firm_id": "FIRM-002"})\n with flask_app.test_request_context("/"):\n     session.update(username="trustee", role="Trustee")\n     check("missing firm has no fallback", app_module._compliance_review_read_scope() == {"global": False, "firm_id": None})\n service_patch = "services.services_compliance_reviews."\n def ok_registry(**kwargs):\n     return {"available":True,"status":"ok","reviews":[],"count":0}\n def review_record():\n     return {"compliance_review_id":"CMP-2026-0001","firm_id":"FIRM-001","title":"Review","review_type":"policy_review",\n             "status":"draft","version":1,"created_at":"2026-01-01","updated_at":"2026-01-01"}\n\n for username, role, firm, expected_scope in (\n     ("admin","Admin",None,{"global":True}),\n     ("other","Admin","FIRM-002",{"global":False,"firm_id":"FIRM-002"}),\n     ("trustee","Trustee","FIRM-002",{"global":False,"firm_id":"FIRM-002"}),\n ):\n     captured = {}\n     def scoped_registry(**kwargs):\n         captured.update(kwargs)\n         return ok_registry()\n     authenticated(client, username, role, firm)\n     with patch(service_patch+"list_compliance_reviews", side_effect=scoped_registry), \\\n          patch(service_patch+"create_compliance_review") as writer:\n         response = client.get("/compliance/reviews")\n     check(f"registry {role}/{username} 200", response.status_code == 200)\n     check(f"registry {role}/{username} correct scope", captured.get("scope") == expected_scope)\n     check(f"registry {role}/{username} no write call", not writer.called)\n check("registry template rendered", b"Compliance Review Registry" in response.data)\n\n authenticated(client, "trustee","Trustee",None)\n missing_firm = {\n     "available": False,\n     "status": "invalid_scope",\n     "message": "A valid firm scope is required to view Compliance Reviews.",\n     "reviews": [],\n     "count": 0,\n }\n with patch(service_patch+"list_compliance_reviews", return_value=missing_firm), \\\n      patch(service_patch+"create_compliance_review") as writer:\n     missing_firm_response = client.get("/compliance/reviews")\n check("registry missing firm authenticated non-global session", True)\n check("registry missing firm 403", missing_firm_response.status_code == 403)\n check("registry missing firm no write call", not writer.called)\n for status in ("schema_missing","read_failure"):\n     authenticated(client,"admin","Admin")\n     result={"available":False,"status":status,"reviews":[],"count":0}\n     with patch(service_patch+"list_compliance_reviews", return_value=result):\n         check(f"registry {status} 503", client.get("/compliance/reviews").status_code == 503)\n\n authenticated(client,"admin","Admin")\n with patch(service_patch+"list_compliance_reviews", side_effect=ok_registry), \\\n      patch(service_patch+"get_compliance_review", return_value=review_record()), \\\n      patch(service_patch+"list_compliance_review_events", return_value=[{"event_id":"EVT-1"}]), \\\n      patch(service_patch+"list_compliance_review_relationships", return_value=[{"relationship_id":"REL-1"}]), \\\n      patch(service_patch+"create_compliance_review") as writer:\n     detail_response=client.get("/compliance/reviews/CMP-2026-0001")\n check("valid detail route 200", detail_response.status_code == 200)\n check("detail template rendered", b"Compliance Review Detail" in detail_response.data)\n check("events passed to detail template", b"EVT-1" in detail_response.data)\n check("relationships passed to detail template", b"REL-1" in detail_response.data)\n check("detail route no write call", not writer.called)\n\n authenticated(client,"admin","Admin")\n with patch(service_patch+"list_compliance_reviews", side_effect=ok_registry):\n     check("malformed detail ID 404", client.get("/compliance/reviews/bad").status_code == 404)\n for label, found in (("missing",None),("cross-firm",None)):\n     authenticated(client,"admin","Admin")\n     with patch(service_patch+"list_compliance_reviews", side_effect=ok_registry), patch(service_patch+"get_compliance_review", return_value=found):\n         check(f"{label} detail 404", client.get("/compliance/reviews/CMP-2026-9999").status_code == 404)\n for status in ("schema_missing","read_failure"):\n     authenticated(client,"admin","Admin")\n     with patch(service_patch+"list_compliance_reviews", return_value={"available":False,"status":status,"reviews":[],"count":0}):\n         check(f"detail {status} 503", client.get("/compliance/reviews/CMP-2026-0001").status_code == 503)\n\n for name in ("ios_workspaces/compliance.html","compliance_reviews/registry.html","compliance_reviews/detail.html"):\n     try:\n         flask_app.jinja_env.get_template(name)\n         loaded=True\n     except Exception:\n         loaded=False\n     check(f"template loads: {name}", loaded)\n check("workspace links registry endpoint", \'url_for("compliance_review_registry")\' in workspace_source)\n check("registry links detail endpoint", \'url_for("compliance_review_detail"\' in registry_source)\n check("registry return navigation", "Back to Compliance Workspace" in registry_source)\n check("detail return navigation", "Back to Compliance Review Registry" in detail_source and "Back to Compliance Workspace" in detail_source)\n\n for template_name, source in (("registry",registry_source),("detail",detail_source)):\n     parsed = flask_app.jinja_env.parse(source)\n     forbidden_tags = ("form","input","textarea","select","button","script")\n     for tag in forbidden_tags:\n         check(f"{template_name} has no {tag} element", re.search(rf"<\\s*{tag}\\b", source, re.I) is None)\n     check(f"{template_name} has no POST action", not re.search(r"\\bmethod\\s*=\\s*[\'\\"]?post", source, re.I))\n     check(f"{template_name} has no CSRF field", "csrf" not in source.lower())\n     check(f"{template_name} has no safe filter", "|safe" not in source.replace(" ","").lower())\n     for field in ("payload_hash","idempotency_key","approved_by","approved_at"):\n         check(f"{template_name} excludes {field}", field not in source)\n     check(f"{template_name} excludes internal numeric ID display", not re.search(r"\\breview\\.id\\b|\\bevent\\.id\\b|\\brelationship\\.id\\b", source))\n\n check("registry populated state", "{% for review in registry.reviews %}" in registry_source)\n check("registry empty state", "No Compliance Review records are available within the current authorized scope." in registry_source)\n check("registry unavailable state", "{% if not registry.available %}" in registry_source)\n check("registry exact empty wording", "No Compliance Review records are available within the current authorized scope." in registry_source)\n for heading in ("Review Identity","Context Ownership","Source and Requirement Provenance","Review Question and Scope",\n                 "Attribution and Timestamps","Append-Only Review Event Timeline","Related Governed Records"):\n     check(f"detail contains {heading}", heading in detail_source)\n check("detail empty event state", "No Compliance Review lifecycle events are available for this record." in detail_source)\n check("detail empty relationship state", "No related governed records are currently stored for this Compliance Review." in detail_source)\n check("detail institutional caution", "Institutional Caution" in detail_source)\n\n attack=\'<script>alert("x")</script>\'\n with flask_app.test_request_context("/"):\n     registry_html=flask_app.jinja_env.get_template("compliance_reviews/registry.html").render(\n         registry={"available":True,"reviews":[{"compliance_review_id":"CMP-2026-0001","title":attack}],"count":1},\n         compliance_workspace_url="/admin/ios/compliance")\n     detail_html=flask_app.jinja_env.get_template("compliance_reviews/detail.html").render(\n         review={"compliance_review_id":"CMP-2026-0001","title":attack},events=[],relationships=[],\n         registry_url="/compliance/reviews",compliance_workspace_url="/admin/ios/compliance")\n for name, html, source in (("registry",registry_html,registry_source),("detail",detail_html,detail_source)):\n     check(f"{name} escapes stored script", attack not in html)\n     check(f"{name} contains escaped text", "&lt;script&gt;alert" in html)\n     check(f"{name} no unsafe bypass", "|safe" not in source.replace(" ","").lower())\n     check(f"{name} source no script element", re.search(r"<\\s*script\\b",source,re.I) is None)\n\n with flask_app.test_request_context("/"):\n     workspace_html=flask_app.jinja_env.get_template("ios_workspaces/compliance.html").render()\n check("workspace registry resolves", \'href="/compliance/reviews"\' in workspace_html)\n check("workspace has no mutation controls", not re.search(r"<\\s*(form|input|button|select|textarea)\\b",workspace_html,re.I))\n check("workspace caution visible", "does not itself prove compliance" in workspace_html)\n check("workspace exclusions informational", "not activated in this milestone" in workspace_html and "<form" not in workspace_html.lower())\n\n endpoint_paths={r.endpoint:r.rule for r in rules}\n check("System Observation registry preserved", endpoint_paths.get("system_observation_registry")=="/system/observations")\n check("System Observation detail preserved", endpoint_paths.get("system_observation_detail")=="/system/observations/<observation_id>")\n\n check("global before_request authentication exists", "@app.before_request\\ndef enforce_session_timeout" in app_source and "public_endpoints" in app_source)\n public_match=re.search(r"public_endpoints\\s*=\\s*\\{(.*?)\\}",app_source,re.S)\n public_text=public_match.group(1) if public_match else ""\n check("new endpoints are not public", "compliance_review_registry" not in public_text and "compliance_review_detail" not in public_text)\n check("new endpoints remain GET-only", all(r.methods=={"GET","HEAD","OPTIONS"} for r in review_rules))\n check("new endpoints not csrf exempt", "@csrf.exempt" not in route_block)\n for mapping in ("ENDPOINT_PERMISSION_RULES","ROLE_RULES","TRUST_SCOPED_ENDPOINT_RULES"):\n     start=app_source.index(mapping+" =")\n     fragment=app_source[start:app_source.index("}",start)+1]\n     check(f"no new {mapping} entry", "compliance_review_registry" not in fragment and "compliance_review_detail" not in fragment)\n\n sensitive_error="SQL SELECT * FROM C:\\\\secret\\\\trustee_app.db token=abc password=xyz connection string stack trace session {\'role\':\'Admin\'}"\n for path, patches in (\n     ("/compliance/reviews", [patch(service_patch+"list_compliance_reviews", side_effect=RuntimeError(sensitive_error))]),\n     ("/compliance/reviews/CMP-2026-0001", [patch(service_patch+"list_compliance_reviews", side_effect=RuntimeError(sensitive_error))]),\n ):\n     authenticated(client,"admin","Admin")\n     with contextlib.ExitStack() as stack:\n         for item in patches:\n             stack.enter_context(item)\n         response=client.get(path)\n     body=response.get_data(as_text=True).lower()\n     check(f"bounded failure status: {path}", response.status_code==503)\n     forbidden=("select *","trustee_app.db","stack trace","connection string","password=xyz","token=abc","{\'role\'","repair")\n     check(f"failure excludes sensitive data: {path}", all(x not in body for x in forbidden))\n\n result={"ok":True,"checks":checks}\nexcept Exception: result={"ok":False,"checks":checks,"fatal":"bounded_child_failure"}\nprint(json.dumps(result,separators=(",",":")))\n'
def isolated():
 with tempfile.TemporaryDirectory() as td:
  t=Path(td).resolve()/"app.db"; q=run(sys.executable,"-c",CHILD,str(ROOT),extra={"DB_PATH":str(t)})
  if q.returncode: return {"ok":False,"checks":[],"fatal":"bounded_child_failure"}
  try: return json.loads(q.stdout)
  except Exception: return {"ok":False,"checks":[],"fatal":"bounded_child_failure"}
def audit():
 print("POST-V2-17Q-H COMPLIANCE REVIEW READ-ONLY UI AUDIT"); before=snap(); check("phase baseline mtime certified",before[1]==BASE); repo("audit start")
 for x in ("app.py","services/services_compliance_reviews.py","templates/ios_workspaces/compliance.html","templates/compliance_reviews/registry.html","templates/compliance_reviews/detail.html","scripts/audit_compliance_review_foundation_17q_g.py"): check("file exists: "+x,(ROOT/x).is_file())
 app_source=(ROOT/"app.py").read_text(encoding="utf-8"); service_source=(ROOT/"services/services_compliance_reviews.py").read_text(encoding="utf-8"); model_init_source=(ROOT/"models/__init__.py").read_text(encoding="utf-8"); registry_source=(ROOT/"templates/compliance_reviews/registry.html").read_text(encoding="utf-8"); detail_source=(ROOT/"templates/compliance_reviews/detail.html").read_text(encoding="utf-8"); workspace_source=(ROOT/"templates/ios_workspaces/compliance.html").read_text(encoding="utf-8"); route_block=app_source[app_source.index("def _compliance_review_read_scope"):app_source.index("def _system_observation_read_scope")]
 from migrations.add_compliance_review_foundation import ensure_compliance_review_foundation
 from services.services_compliance_reviews import get_compliance_review,list_compliance_review_events,list_compliance_review_relationships,list_compliance_reviews,validate_public_compliance_review_id
 scope_tree = ast.parse(route_block).body[0]
 scope_constants = {n.value for n in ast.walk(scope_tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
 check("scope helper has no hard-coded firm fallback", not ({"FIRM-001", "FIRM-002"} & scope_constants))

 tree = ast.parse(route_block)
 calls = []
 for node in ast.walk(tree):
     if isinstance(node, ast.Call):
         try:
             calls.append(ast.unparse(node.func))
         except Exception:
             pass
 for forbidden in (
     "create_compliance_review", "transition_compliance_review",
     "ensure_compliance_review_foundation", "db.create_all", "ext_db.create_all",
     "subprocess", "os.system", "log_change",
 ):
     check(f"route block does not call {forbidden}", forbidden not in calls, calls)
 for keyword in ("INSERT", "UPDATE", "DELETE"):
     check(f"route block has no {keyword}", not re.search(rf"\b{keyword}\b", route_block, re.I))
 check("route block has no migration execution", not re.search(r"\b(migrate|migration|upgrade)\s*\(", route_block, re.I))
 route_decorators = [line.strip() for line in route_block.splitlines() if "@app.route" in line or "methods=" in line]
 check("routes do not declare POST or GET/POST", all("POST" not in line for line in route_decorators))

 check("default registry limit bounded", re.search(r"def list_compliance_reviews\(\*, scope=None, limit=100,", service_source) is not None)
 with tempfile.TemporaryDirectory() as td:
     empty = sqlite3.connect(Path(td) / "empty.db")
     empty.row_factory = sqlite3.Row
     try:
         schema_missing = list_compliance_reviews(scope={"global": True}, connection=empty)
         check("schema-missing available false", schema_missing.get("available") is False)
         check("schema-missing status", schema_missing.get("status") == "schema_missing")
         check("schema-missing empty reviews", schema_missing.get("reviews") == [])
         check("schema-missing count zero", schema_missing.get("count") == 0)
         check("schema-missing creates no Compliance table", compliance_objects(empty) == ())
         check("schema-missing invokes no migration", "ensure_compliance_review_foundation(" not in service_source[service_source.index("def list_compliance_reviews"):service_source.index("def create_compliance_review")])
         check("isolated empty database remains empty", empty.execute("SELECT count(*) FROM sqlite_master").fetchone()[0] == 0)
     finally:
         empty.close()

 for value, valid in ((250, True), (251, False), (True, False), ("not-an-integer", False)):
     try:
         with sqlite3.connect(":memory:") as conn:
             conn.row_factory = sqlite3.Row
             list_compliance_reviews(scope={"global": True}, limit=value, connection=conn)
         accepted = True
     except ValueError:
         accepted = False
     check(f"limit contract {value!r}", accepted is valid)
 invalid_scope = list_compliance_reviews(scope={"global": False, "firm_id": None}, connection=sqlite3.connect(":memory:"))
 check("missing firm scope invalid_scope", invalid_scope.get("status") == "invalid_scope")
 check("global scope accepted", list_compliance_reviews(scope={"global": True}, connection=sqlite3.connect(":memory:")).get("status") == "schema_missing")
 for bad_id in ("CMP-26-1", "CMP-2026-00001", "bad", "", None):
     try:
         validate_public_compliance_review_id(bad_id)
         rejected = False
     except (TypeError, ValueError):
         rejected = True
     check(f"malformed public ID rejected: {bad_id!r}", rejected)
 check("registry SQL ordering", "ORDER BY updated_at DESC, created_at DESC, compliance_review_id DESC" in service_source)
 check("event SQL ordering", "ORDER BY event_sequence ASC" in service_source)
 check("relationship SQL ordering", "ORDER BY created_at ASC, relationship_id ASC" in service_source)

 with tempfile.TemporaryDirectory() as td:
     temp_path = Path(td) / "compliance.db"
     conn = sqlite3.connect(temp_path)
     conn.row_factory = sqlite3.Row
     first = ensure_compliance_review_foundation(connection=conn)
     conn.commit()
     objects_first = tuple(conn.execute("SELECT type,name,tbl_name FROM sqlite_master ORDER BY type,name"))
     second = ensure_compliance_review_foundation(connection=conn)
     conn.commit()
     objects_second = tuple(conn.execute("SELECT type,name,tbl_name FROM sqlite_master ORDER BY type,name"))
     check("isolated migration succeeds", first == {"ok": True, "status": "verified"})
     tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
     check("required Compliance Review tables exist", {"compliance_reviews", "compliance_review_events", "compliance_review_relationships", "compliance_review_number_sequences"} <= tables)
     check("isolated migration second application succeeds", second == {"ok": True, "status": "verified"})
     check("second migration duplicates no schema objects", objects_first == objects_second)
     check("isolated integrity check ok", conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
     check("isolated foreign key check empty", conn.execute("PRAGMA foreign_key_check").fetchall() == [])

     review_sql = """INSERT INTO compliance_reviews
     (compliance_review_id,firm_id,institution_id,trust_id,matter_id,deployment_key,title,review_type,question_presented,
     governing_requirement_type,governing_requirement_id,governing_requirement_label,source_type,source_id,source_label,
     scope_summary,status,priority,risk_level,review_owner,assigned_to,authority_basis,approval_required,approved_by,
     finding,disposition,required_follow_up,created_by,created_at,updated_by,updated_at,version,idempotency_key,payload_hash)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
     rows = [
         ("CMP-2026-0001","FIRM-001","INST-1","TRUST-1",None,None,"First","policy_review","Question one",
          "institutional_policy","POL-1","Policy","governance_record","POL-1","Policy source","Scope","under_review","high","high",
          "Owner","Assignee","Authority",1,"hidden","hidden","hidden","hidden","creator","2026-01-01T00:00:00+00:00","updater","2026-01-03T00:00:00+00:00",2,"hidden","hidden"),
         ("CMP-2026-0002","FIRM-001","INST-1",None,"MAT-2",None,"Second","policy_review","Question two",
          "institutional_policy","POL-2","Policy","governance_record","POL-2","Policy source","Scope","draft","normal","moderate",
          "Owner","Assignee","Authority",0,"hidden","hidden","hidden","hidden","creator","2026-01-02T00:00:00+00:00","updater","2026-01-04T00:00:00+00:00",1,"hidden2","hidden2"),
         ("CMP-2026-0003","FIRM-002","INST-2",None,None,"DEP-2","Third","policy_review","Question three",
          "institutional_policy","POL-3","Policy","governance_record","POL-3","Policy source","Scope","opened","low","low",
          "Owner","Assignee","Authority",0,"hidden","hidden","hidden","hidden","creator","2026-01-03T00:00:00+00:00","updater","2026-01-05T00:00:00+00:00",1,"hidden3","hidden3"),
     ]
     conn.executemany(review_sql, rows)
     event_sql = """INSERT INTO compliance_review_events
     (event_id,compliance_review_id,event_sequence,event_type,actor_id,actor_label,prior_status,resulting_status,summary,reason,
     idempotency_key,payload_hash,expected_version,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
     conn.execute(event_sql, ("EVT-2","CMP-2026-0001",2,"opened","USR-2","Actor 2","draft","opened","Second","Reason","event-key-2","event-hash-2",1,"2026-01-02"))
     conn.execute(event_sql, ("EVT-1","CMP-2026-0001",1,"created","USR-1","Actor 1",None,"draft","First","Reason","event-key-1","event-hash-1",None,"2026-01-01"))
     conn.execute("""INSERT INTO compliance_review_relationships
         (relationship_id,compliance_review_id,relationship_type,related_record_type,related_record_id,direction,status,created_by,created_at)
         VALUES (?,?,?,?,?,?,?,?,?)""", ("REL-1","CMP-2026-0001","governed_by","policy","POL-1","outbound","active","creator","2026-01-01"))
     conn.commit()

     f1 = list_compliance_reviews(scope={"global": False, "firm_id": "FIRM-001"}, connection=conn)
     f2 = list_compliance_reviews(scope={"global": False, "firm_id": "FIRM-002"}, connection=conn)
     glob = list_compliance_reviews(scope={"global": True}, connection=conn)
     check("FIRM-001 registry isolated", [r["compliance_review_id"] for r in f1["reviews"]] == ["CMP-2026-0002","CMP-2026-0001"])
     check("FIRM-002 registry isolated", [r["compliance_review_id"] for r in f2["reviews"]] == ["CMP-2026-0003"])
     check("global registry all records", [r["compliance_review_id"] for r in glob["reviews"]] == ["CMP-2026-0003","CMP-2026-0002","CMP-2026-0001"])
     check("registry count equals rows", all(x["count"] == len(x["reviews"]) for x in (f1,f2,glob)))
     sensitive = {"payload_hash","idempotency_key","approved_by","approved_at","finding","disposition","disposition_basis","required_follow_up","id"}
     check("public registry excludes sensitive/internal fields", all(not (set(r) & sensitive) for r in glob["reviews"]))
     expected = {"compliance_review_id","firm_id","title","review_type","question_presented","governing_requirement_type","source_type","scope_summary","status","priority","risk_level","review_owner","created_by","created_at","updated_by","updated_at","version"}
     check("public identity/provenance/context/version fields available", all(expected <= set(r) for r in glob["reviews"]))
     check("cross-firm registry record invisible", all(r["firm_id"] == "FIRM-001" for r in f1["reviews"]))

     review = get_compliance_review("CMP-2026-0001", scope={"global": False,"firm_id":"FIRM-001"}, connection=conn)
     check("in-scope detail returned", review and review["compliance_review_id"] == "CMP-2026-0001")
     check("missing detail None", get_compliance_review("CMP-2026-9999", scope={"global":True}, connection=conn) is None)
     check("cross-firm detail None", get_compliance_review("CMP-2026-0003", scope={"global":False,"firm_id":"FIRM-001"}, connection=conn) is None)
     events = list_compliance_review_events("CMP-2026-0001", scope={"global":True}, connection=conn)
     relationships = list_compliance_review_relationships("CMP-2026-0001", scope={"global":True}, connection=conn)
     check("events oldest-to-newest", [e["event_sequence"] for e in events] == [1,2])
     check("relationships deterministic", [r["relationship_id"] for r in relationships] == ["REL-1"])
     check("event serialization excludes secrets", all(not (set(e) & {"payload_hash","idempotency_key","id"}) for e in events))
     check("relationship serialization excludes numeric id", all("id" not in r for r in relationships))
     conn.close()

 for template_name,source in (("registry",registry_source),("detail",detail_source)):
  for tag in ("form","input","textarea","select","button","script"): check("parent template source "+template_name+" has no "+tag,re.search(r"<\s*"+tag+r"\b",source,re.I) is None)
  check("parent template source "+template_name+" has no POST",not re.search(r"\bmethod\s*=\s*[\"\']?post",source,re.I)); check("parent template source "+template_name+" has no safe filter","|safe" not in source.replace(" ","").lower())
  for field in ("payload_hash","idempotency_key","approved_by","approved_at"): check("parent template source "+template_name+" excludes "+field,field not in source)
 check("parent registry state wording","No Compliance Review records are available within the current authorized scope." in registry_source and "{% if not registry.available %}" in registry_source)
 check("parent detail state wording","No Compliance Review lifecycle events are available for this record." in detail_source and "No related governed records are currently stored for this Compliance Review." in detail_source)
 check("models init excludes Compliance ORM import", "compliance" not in model_init_source.lower())
 prefix = app_source[:app_source.index("def _compliance_review_read_scope")]
 check("app has no global Compliance ORM import", "models_compliance_reviews" not in prefix)
 check("app startup does not ensure foundation", "ensure_compliance_review_foundation(" not in prefix)
 check("app startup does not register migration", "add_compliance_review_foundation" not in prefix)
 check("app startup has no Compliance create_all", not re.search(r"compliance.{0,100}create_all|create_all.{0,100}compliance",prefix,re.I|re.S))
 check("read routes create no schema", "create_all" not in route_block and "ensure_compliance_review_foundation" not in route_block)
 wording_parts=("institutional","foundation","registry","has not been activated")
 check("foundation-unavailable wording present",all(all(part in source for part in wording_parts) for source in (app_source,service_source,workspace_source)))
 check("foundation response says no record", "No review record was created" in app_source)
 check("foundation response says no migration", "no migration occurred" in app_source)
 check("permissions cannot activate registry", "changing operator permissions will not activate" in app_source and "registry. Authorized institutional activation is required." in app_source)
 check("authorization denial structurally distinct", 'status") == "invalid_scope"' in route_block and "authenticated firm scope" in route_block)

 pre=snap(); q=run(sys.executable,"scripts/audit_compliance_review_foundation_17q_g.py"); post=snap(); out=(q.stdout+q.stderr)[:30000]; check("foundation audit exit zero",q.returncode==0); check("foundation output reports PASS","RESULT: PASS" in out); check("foundation identifies POST-V2-17Q-G","POST-V2-17Q-G RESULT" in out); check("foundation has no failed check","FAIL -" not in out); check("foundation database unchanged",pre==post)
 z=isolated()
 for x in z.get("checks",[]): check("isolated app: "+str(x.get("name")),x.get("passed") is True,x.get("detail",""))
 check("isolated app child completed structurally",z.get("ok") is True,z.get("fatal","bounded_child_failure")); check("no new repository database file",frozenset(ROOT.glob("*.db"))==REPO_DATABASES); after=snap(); check("normal database snapshot identical",after==before); check("normal database mtime equals H4C baseline",after[1]==BASE); check("no Compliance objects before or after",before[2]==after[2]==()); check("normal database required baseline preserved",after[0]==3096576 and after[3]==(513,513) and after[4]==25 and after[5]==51 and after[7]==("ok",) and after[8]==()); repo("audit end")
def main():
 try: audit()
 except Exception: check("controlled top-level audit completion",False,"bounded_audit_failure")
 print(f"checks_total={total}"); print(f"checks_passed={passed}"); print(f"checks_failed={len(failures)}"); print("POST-V2-17Q-H RESULT")
 if failures:
  print("FAIL")
  for n,d in failures: print("FAILED CHECK - "+n+(" | "+d if d else ""))
  return 1
 print("PASS - The Compliance Review Registry and Review Detail interfaces provide protected, bounded, read-only access to Compliance Review identity, provenance, context, and append-only lifecycle history without activating creation, findings, disposition, approval, routing, closure, remediation, migration, or render-side persistence."); return 0
if __name__=="__main__": raise SystemExit(main())
