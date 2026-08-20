# V3 Account/Asset Read Aggregation Contract

Status: canonical read aggregation established by `V3-SVC-AA-1`.

## Canonical owner and sources

`services/services_account_asset_contract.py` owns the reusable aggregation
boundary. `database/db.py` and the `accounts` and `properties` tables remain
persistence owners. The boundary reuses `services/services_trust_contract.py`
for authenticated Trust-context validation.

## Public interface

- `list_trust_accounts(trust_id, *, authorization_check)`
- `get_trust_account(account_id, trust_id, *, authorization_check)`
- `list_trust_assets(trust_id, *, authorization_check)`
- `get_trust_asset(property_id, trust_id, *, authorization_check)`
- `aggregate_trust_inventory(trust_id, *, authorization_check)`

## Scope and safe failure

Every operation first requires a Trust visible through the canonical Trust read
contract. Account and property SQL then requires both the active `firm_id` and
the exact `trust_id`; individual reads additionally require the record ID.
Missing, denied, wrong-Trust, and cross-firm records return the same safe absent
result. No all-firms aggregation exists.

The facade performs a read-only schema preflight and fails closed if accounts or
properties lack firm/Trust scope columns. It does not invoke legacy helpers that
may add columns during a nominal read.

## Result contract and sensitive-data exclusion

Accounts expose only identifiers, type, institution, label, masked number,
purpose, property reference, firm/Trust scope, and source attribution. Passwords,
PINs, tokens, recovery material, full credentials, and unapproved secret fields
are never copied, even if a legacy table contains them.

Assets expose property identity/type/class, safe identifier metadata, relevant
dates/status, responsible party, custodian, and existing continuity/custody
classifications with `source: properties`. Notes, evidence bodies, custody
events, archive content, and unsupported valuations are excluded.

The aggregate contains the canonical Trust identity, source-attributed account
and property arrays, counts, unresolved account-to-property reference count,
and an explicit `accounts_and_properties_only` completeness label. It does not
claim a complete financial, legal, custody, or handoff inventory.

## Ownership boundaries

- Continuity owns readiness, preservation requirements, custody events, evidence
  profiles, and activation behavior. This facade only reports classifications
  already stored on the property row and does not call the currently unscoped
  continuity-asset readers.
- Accounting and ledger owners retain balances, entries, chart-of-accounts,
  recognition, tax, and valuation calculations.
- Archive/custody owners retain packets, integrity, finalization, and evidence.
- Transfer/funding owners retain ownership movement and execution state.
- Digital Continuity accounts remain metadata/vault-reference records and are
  not reclassified as financial accounts here.

## Read-only and compatibility guarantees

No public function creates, links, unlinks, updates, deletes, posts, seeds,
scores, generates, or audits records. No chart of accounts is seeded and no
ordinary read emits a custody, archive, transfer, readiness, or audit event.
Existing routes, DB helpers, reports, Trust, Fiduciary, Governance, Continuity,
Execution, tax, and export callers remain unchanged.

## Known limitations and future consumers

Account status is NOT DOCUMENTED in the current base schema. Balances,
valuations, obligations, legal ownership conclusions, custody completeness, and
continuity readiness are outside this contract. Trust, Documents, Execution,
Archive, and a future successor-handoff consumer may reuse the inventory as a
source-attributed read snapshot only; no such integration is implemented here.
