# vendor-lifecycle-tracker

A small Python tool that checks third-party vendors against the stage gates of a vendor lifecycle: intake, due diligence, approval, go-live, periodic reassessment and offboarding. It finds vendors that skipped a gate, went live without approval, stalled in a stage, are overdue for reassessment, or were offboarded without the access, data and contract clean-up.

Python standard library only (tested on Python 3.13).

> **Data note.** `examples/sample_vendors.json` is **synthetic**. Ten of the 30 vendors have lifecycle problems injected on purpose, and the tests check the tool finds exactly those. Nothing here comes from a real organisation.

## Lifecycle

```
intake -> due_diligence -> approved -> active <-> reassessment -> offboarding -> offboarded
                       \-> rejected
```

Each vendor carries its current `stage` and a dated `history`. The history must end at the current stage and its dates must not go backwards (otherwise the input is rejected, exit code 2).

## Quick start

```bash
python3 -m vlt examples/sample_vendors.json --as-of 2026-10-23 --out-dir out   # report.md, report.json, issues.csv
python3 -m vlt examples/sample_vendors.json --fail-on high                     # exit 1 on any high or critical issue
python3 -m unittest discover -s tests                                          # 24 tests
bash scripts/run_demo.sh                                                       # regenerate data, report and tests
```

## Checks

| Check | Raised when |
|---|---|
| `SKIPPED_GATE` | History jumps forward past a stage (for example intake straight to active) |
| `INVALID_TRANSITION` | History moves in a way the lifecycle does not allow (for example offboarded back to active) |
| `GO_LIVE_WITHOUT_APPROVAL` | Vendor is or was live with no approval or no named approver (critical for Tier 1, then high, medium, low) |
| `DUE_DILIGENCE_INCOMPLETE` | Approved or live, but the checklist is incomplete or a required DPA is unsigned |
| `TIER_MISSING` | A live vendor has no risk tier |
| `STALLED_STAGE` | Too long in intake, due diligence, approved or offboarding |
| `REASSESSMENT_OVERDUE` | Live vendor never assessed, or past the tier cadence (Tier 1-2: 12 months, Tier 3: 24, Tier 4: 36) |
| `OFFBOARD_INCOMPLETE` | Marked offboarded with access, data disposal, contract or register steps undone (critical if access was not revoked) |
| `OFFBOARD_ACCESS_LINGERING` | Offboarded with access, or in offboarding past the limit with access |

Thresholds and checklists are in `vlt/config.json`.

## Limitations

- **The lifecycle and cadences are illustrative defaults**, not a standard. Adjust them to your TPRM policy.
- **The checklist items are flags you maintain.** The tool does not verify that questionnaires were read well or that access was really removed; `active_access` should come from your IAM records.
- **Tiering is an input.** This tool checks the lifecycle, not how the tier was decided (see `tprm-monitor` for a scoring model).
- No persistence, UI or authentication. It reads JSON and writes reports.

## Layout

```
vlt/       models.py  analyse.py  report.py  config.json  __main__.py
tools/     gen_sample.py     synthetic data generator
tests/     24 tests          incl. an exact-match end-to-end test
examples/  sample_vendors.json  report.md  report.json  issues.csv
scripts/   run_demo.sh
```
