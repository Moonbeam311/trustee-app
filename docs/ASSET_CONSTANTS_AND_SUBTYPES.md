# Asset Constants and Subtypes Doctrine

## Core Principle
The asset classes are now treated as locked baseline constants across the system. They should remain consistently available throughout the build as the canonical asset taxonomy.

## Locked Core Asset Classes
- real_property
- tangible_property
- financial_property
- business_interest
- intellectual_property
- digital_property
- contractual_right
- ucc_secured_interest
- other

## Important Clarification
These locked classes are the stable system-wide model. They are not intended to prevent expansion. Instead:
- asset_class = stable constant layer
- asset_subtype = flexible expansion layer

## Examples
- digital_property -> website
- intellectual_property -> curriculum
- intellectual_property -> recipe collection
- ucc_secured_interest -> UCC filing
- business_interest -> LLC interest

## Product Meaning
This preserves both architectural consistency and practical flexibility. The system can remain stable while supporting growth into many different wealth and control categories.

## Implementation Expectation
These classes should remain available across:
- asset entry forms
- asset dashboard filters
- asset detail pages
- trust summaries
- reports and packet generation
- future intelligence layers

## Related Constant System Areas
Alongside asset classes, other structural constants should remain stable across the build, including:
- trust statuses
- major workflow states
- core relationship model: trust -> asset -> account -> document -> ledger