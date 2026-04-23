---
status: accepted
contract: id-taxonomy
applies_to: [pvs-x-isynet]
helper: makeIdHelper
hoist_when:
  condition: second_package_implements_contract
  contract: id-taxonomy
  target: adapter-common
  trigger_bead_title: '[HOIST] makeIdHelper to adapter-common'
---

# ADR-001: ID Taxonomy

All entity IDs must use typed helpers, not raw strings.
