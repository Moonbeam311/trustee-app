# HOS-WEB-1B — Work & Learning Hub Product Architecture

Date: 2026-08-15
Status: Public product architecture grounded in a read-only authenticated capability audit
Locked public name: **Work & Learning Hub**

## 1. Purpose

The Work & Learning Hub is the proposed unifying environment for protected exploratory work in Hindsfoot OS. It is intended to connect learning, questions, working notes, program development, sources, unresolved issues, review, and deliberate promotion without confusing drafts with institutional facts.

## 2. User need

Consequential work rarely begins as a finished record. An authorized person needs a durable place to learn terminology, ask questions, compare approaches, record assumptions, preserve context, and prepare material for review before any governed action occurs.

## 3. Verified current capabilities

The following authenticated components are implemented, although they are not yet unified under the Work & Learning Hub name:

| ID | Capability | Classification | Source evidence |
|---|---|---|---|
| V-01 | Published learning articles, categories, trust-type material, and form guides | VERIFIED IMPLEMENTED | `app.py`: `learning_dashboard`, `learning_category`, `learning_article`, `forms_dashboard`; learning templates |
| V-02 | Tutorial video/media browsing by category and subject | VERIFIED IMPLEMENTED | `app.py`: `video_dashboard`, `video_category`, `video_detail`; video templates |
| V-03 | Firm-scoped planning workspaces with purpose, owner, status, create, detail, and edit surfaces | VERIFIED IMPLEMENTED | `app.py`: `get_all_workspaces`, `get_workspace_by_id`, `create_workspace`, `update_workspace`, workspace routes; workspace templates |
| V-04 | Firm-scoped workspace notes organized by section | VERIFIED IMPLEMENTED | `app.py`: `get_workspace_notes`, `create_workspace_note`, `workspace_note_new`; workspace note templates |
| V-05 | Owner-scoped discussion threads and replies, optionally connected to workspaces | VERIFIED IMPLEMENTED | `app.py`: discussion helpers and route functions; discussion templates |
| V-06 | Workspace-linked tasks and status views | VERIFIED IMPLEMENTED | `app.py`: `workspace_tasks`, `workspace_task_new`; `templates/workspace_tasks.html` |
| V-07 | Workspace-linked draft document surfaces | VERIFIED IMPLEMENTED | `app.py`: `workspace_documents`, `workspace_document_generate`; `templates/workspace_documents.html` |
| V-08 | Authenticated User Guide explaining learning, planning, workspace, discussion, decision, execution, and document modules | VERIFIED IMPLEMENTED | `app.py`: `guide_page`; `templates/guide_page.html`; `tests/test_hos_brand_1.py` |
| V-09 | Authentication, role gates, CSRF checks on writes, and firm-scoped workspace retrieval/mutation | VERIFIED IMPLEMENTED | `app.py`: `enforce_session_timeout`, `ROLE_RULES`, workspace helpers and route guards |

Verified implemented count: **9**.

## 4. Adjacent existing capabilities

These systems substantiate the governed-review model but are not currently a unified Work & Learning Hub workflow:

| ID | Capability | Classification | Source evidence |
|---|---|---|---|
| A-01 | Reviewable intake-to-trust proposals with explicit operator confirmation | VERIFIED ADJACENT | `routes_tpd1c.py`; `services/services_intake_trust_bridge.py`; TPD tests |
| A-02 | Immutable proposal revisions and ordered governed events | VERIFIED ADJACENT | `database/migrations_intake_trust_bridge.py`; bridge service; `tests/test_tpd1c_bridge_continuity.py` |
| A-03 | Guided drafting, variable binding, preview, section review, and controlled export gates | VERIFIED ADJACENT | guided-draft route functions and `database/db.py` guided workspace tables |
| A-04 | Source-reference and evidence-status structures in other institutional modules | VERIFIED ADJACENT | database source-reference fields; genealogy and bridge evidence conventions |
| A-05 | Institutional audit logging and security-denial history | VERIFIED ADJACENT | application audit helpers, audit report routes, security enforcement |
| A-06 | Read-only Formation Preview Hub with lifecycle restrictions before downstream action | VERIFIED ADJACENT | `templates/trust_formation_preview_hub.html`; TPD route and lifecycle tests |

Verified adjacent count: **6**.

## 5. Planned capability gaps

| ID | Gap | Classification |
|---|---|---|
| P-01 | One unified Work & Learning Hub route, navigation model, and context builder | ARCHITECTURALLY PLANNED |
| P-02 | A first-class question organizer connected to relevant learning resources | ARCHITECTURALLY PLANNED |
| P-03 | Tailored-program structures for goals, alternatives, scenarios, and revisions | ARCHITECTURALLY PLANNED |
| P-04 | First-class assumption, gap, and unresolved-issue records | ARCHITECTURALLY PLANNED |
| P-05 | Hub-specific attributable source/reference relationships | ARCHITECTURALLY PLANNED |
| P-06 | Saved session continuity and authorized successor handoff | ARCHITECTURALLY PLANNED |
| P-07 | Explicit, transactional promotion from approved working material into a proposal, decision, task, document, or governed record | ARCHITECTURALLY PLANNED |
| P-08 | Unified hub provenance and audit history spanning exploration through promotion | ARCHITECTURALLY PLANNED |

Architecturally planned count: **8**.

## 6. Three-state model

1. **Explore and Learn** — ask questions, review educational resources, understand terminology, identify possibilities, and gather sources.
2. **Work and Develop** — organize goals, compare approaches, record assumptions, identify gaps, test scenarios, and revise a developing program.
3. **Confirm and Govern** — require deliberate human review before approved work becomes a proposal, decision, task, document, workflow instruction, or permanent governed record.

Movement between states is deliberate. No exploratory artifact promotes itself.

## 7. Working-session lifecycle

The planned lifecycle is: create session → establish purpose and authorized context → collect questions and sources → develop goals and alternatives → record assumptions and open issues → revise → mark material ready for review → human review → explicitly promote selected material or return it for more work → preserve the session and outcome.

## 8. Source and reference handling

Each source relationship should identify its origin, title or description, reference, contributor, timestamp, relevance, and evidence status. A source may inform work without proving a conclusion. Conflicts and missing evidence must remain visible.

## 9. Question and answer boundaries

Questions are working artifacts. Responses may provide orientation, relevant educational material, or possible next inquiries, but they are not automatically authoritative. The current application has discussion and learning surfaces; a unified question-and-answer workflow is planned. No automated AI answer system is substantiated.

## 10. Program-development workflow

A tailored program should connect purpose, goals, constraints, alternatives, assumptions, sources, unresolved issues, scenarios, revisions, next steps, and reviewers. Existing workspace purpose, status, notes, discussions, tasks, and documents are building blocks; the unified program model remains planned.

## 11. Draft-to-governed-record promotion

Promotion must be explicit, selective, authorized, firm-scoped, attributable, transactional, and auditable. The source session must remain preserved. Existing TPD confirmation and governed-event mechanisms demonstrate the adjacent pattern; direct Work & Learning Hub promotion is not yet implemented.

## 12. Human confirmation requirements

Human review is required before consequential material changes status. Review must identify what is being confirmed, the source basis, remaining assumptions, the authorized actor, the target record type, and the resulting action. Silence, navigation, time elapsed, or a generated suggestion cannot count as confirmation.

## 13. Permissions and authorized-user boundaries

The current application authenticates nonpublic routes and applies role rules. Workspaces are firm-scoped; discussions are owner-scoped; write routes use role and CSRF controls. The future hub must retain those protections, add explicit session ownership/collaboration rules, and conceal cross-firm records.

## 14. Audit and provenance expectations

Expected events include session creation, source attachment, question or assumption revision, review request, reviewer action, promotion approval or rejection, target creation, and closure. Events must carry stable identities, actor, firm, timestamp, version, and target relationship without storing secrets.

## 15. Continuity and successor-user considerations

An authorized successor should be able to determine what was being developed, why it mattered, which sources informed it, which questions remained open, what was confirmed, and what still required action. Successor access must be explicitly authorized; a complete hub handoff implementation is planned rather than claimed as current.

## 16. Educational/professional-advice boundaries

The hub supports learning, planning, organization, and preparation. It does not replace qualified legal, tax, accounting, investment, financial, genealogical-certification, or other professional advice. Educational material and working discussion do not establish professional conclusions or guaranteed outcomes.

## 17. Public claims matrix

| Public statement | Disposition | Basis |
|---|---|---|
| Hindsfoot provides authenticated learning resources and protected planning workspaces | INCLUDED | V-01 through V-04 and V-09 |
| Users can preserve working notes and revisit workspace context | INCLUDED | V-03 and V-04 |
| Structured discussions can be connected to workspaces | INCLUDED | V-05 |
| Tasks and draft documents can be associated with workspaces | INCLUDED | V-06 and V-07 |
| The Work & Learning Hub is designed around Explore, Develop, and Confirm states | INCLUDED AS PRODUCT ARCHITECTURE | P-01 through P-08 |
| Drafts, questions, and assumptions do not automatically become governed facts | INCLUDED AS GOVERNING PRINCIPLE | Adjacent TPD confirmation and lifecycle evidence |
| The unified hub is fully operational today | WITHHELD | P-01 is not implemented |
| Hindsfoot supplies automated professional analysis or advice | WITHHELD | Not substantiated and prohibited |
| Every question receives a definitive answer | WITHHELD | Not substantiated |
| Drafts automatically promote into institutional records | WITHHELD | Contradicts the governing principle |
| Real-time multiuser collaboration and successor handoff are operational | WITHHELD | Not substantiated as unified hub behavior |

## 18. Future authenticated implementation requirements

Future work requires a bounded contract phase, firm-scoped session schema, role and collaboration model, immutable revision/event model, source relationship model, review queue, explicit promotion policy, transactional service boundary, route-level and service-level authorization, safe UI, migration plan, isolated tests, preservation gates, and browser certification.

Not substantiated count: **5** — AI assistant, automated professional advice, definitive-answer service, automatic promotion, and real-time collaborative/successor handoff.

## 19. Preservation constraints

- Do not reinterpret exploratory work as fact.
- Do not weaken authentication, authorization, firm isolation, CSRF, or lifecycle guards.
- Do not expose authenticated routes, records, identifiers, credentials, or databases publicly.
- Do not merge the public architecture with authenticated implementation without a separate authorized phase.
- Do not modify the locked six-step Hindsfoot operating journey.

## 20. Acceptance criteria

- Public claims remain traceable to this evidence matrix.
- Current and planned capabilities are visibly distinguished.
- The three states are clear and nonautomatic.
- Draft, assumption, source, and confirmation boundaries are explicit.
- Professional-advice limitations are present.
- Public pages contain no authenticated data or paths.
- The locked brand language, master-logo hash, login configuration boundary, six-step journey, and public accessibility baseline remain intact.
