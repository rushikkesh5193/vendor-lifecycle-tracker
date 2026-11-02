# Vendor lifecycle report

As of 2026-10-23. 30 vendors, 15 issues.

## Pipeline

| Stage | Vendors |
|---|---|
| due_diligence | 1 |
| active | 26 |
| offboarding | 1 |
| offboarded | 2 |

## Issues

### Critical (3)

- **GO_LIVE_WITHOUT_APPROVAL** Vendor 001 (`V001`): Vendor is or was live with no recorded approval and approver. *Action:* Obtain and record retrospective approval.
- **OFFBOARD_ACCESS_LINGERING** Vendor 006 (`V006`): Offboarded vendor still has active access. *Action:* Revoke access now.
- **OFFBOARD_INCOMPLETE** Vendor 006 (`V006`): Marked offboarded but not done: access_revoked. *Action:* Finish the offboarding checklist.

### High (8)

- **DUE_DILIGENCE_INCOMPLETE** Vendor 001 (`V001`): Approved or live but missing: tier_assigned, questionnaire_received, evidence_reviewed, dpa_signed. *Action:* Complete the missing due diligence items.
- **REASSESSMENT_OVERDUE** Vendor 001 (`V001`): Live vendor has never been assessed. *Action:* Run an assessment.
- **SKIPPED_GATE** Vendor 001 (`V001`): Moved intake -> active on 2025-02-01, which the lifecycle does not allow. *Action:* Record the missing stage with evidence, or correct the history.
- **GO_LIVE_WITHOUT_APPROVAL** Vendor 002 (`V002`): Vendor is or was live with no recorded approval and approver. *Action:* Obtain and record retrospective approval.
- **TIER_MISSING** Vendor 004 (`V004`): Live vendor has no risk tier. *Action:* Tier the vendor.
- **OFFBOARD_INCOMPLETE** Vendor 007 (`V007`): Marked offboarded but not done: data_disposal_confirmed. *Action:* Finish the offboarding checklist.
- **OFFBOARD_ACCESS_LINGERING** Vendor 008 (`V008`): Offboarding for over the limit and the vendor still has access. *Action:* Revoke access now.
- **DUE_DILIGENCE_INCOMPLETE** Vendor 010 (`V010`): Approved or live but missing: evidence_reviewed. *Action:* Complete the missing due diligence items.

### Medium (4)

- **REASSESSMENT_OVERDUE** Vendor 003 (`V003`): Last assessed 2024-06-01; Tier 3 cadence is 24 months. *Action:* Run the periodic reassessment.
- **STALLED_STAGE** Vendor 005 (`V005`): In due_diligence for 83 days (limit 45). *Action:* Unblock or escalate.
- **STALLED_STAGE** Vendor 008 (`V008`): In offboarding for 69 days (limit 30). *Action:* Unblock or escalate.
- **INVALID_TRANSITION** Vendor 009 (`V009`): Moved offboarded -> active on 2026-01-01, which the lifecycle does not allow. *Action:* Correct the history or reopen the vendor properly.

