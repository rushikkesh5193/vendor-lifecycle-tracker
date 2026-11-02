import json
from pathlib import Path

from .models import ALLOWED, ORDER, SEVERITIES, add_months

SEV = {s: i for i, s in enumerate(SEVERITIES)}


def load_config(path=None):
    return json.loads((Path(path) if path else Path(__file__).with_name("config.json")).read_text(encoding="utf-8"))


def _i(sev, vid, name, check, detail, action):
    return {"severity": sev, "vendor": vid, "name": name, "check": check, "detail": detail, "action": action}


def _tier_sev(tier, top="high"):
    """High-tier vendors get the stronger severity."""
    levels = {"critical": ["critical", "high", "medium", "low"], "high": ["high", "high", "medium", "low"]}[top]
    return levels[(tier or 1) - 1]


def analyse(vendors, cfg=None, as_of=None):
    cfg = cfg or load_config()
    issues, pipeline = [], {}
    for v in vendors:
        pipeline[v["stage"]] = pipeline.get(v["stage"], 0) + 1
        vid, nm, st, tier = v["id"], v["name"], v["stage"], v["tier"]
        hist = v["history"]
        reached = {h["stage"] for h in hist}

        # transitions
        for a, b in zip(hist, hist[1:]):
            if b["stage"] in ALLOWED[a["stage"]]:
                continue
            fwd = a["stage"] in ORDER and b["stage"] in ORDER and ORDER[b["stage"]] > ORDER[a["stage"]]
            issues.append(_i("high" if fwd else "medium", vid, nm, "SKIPPED_GATE" if fwd else "INVALID_TRANSITION",
                             f"Moved {a['stage']} -> {b['stage']} on {b['date']}, which the lifecycle does not allow.",
                             "Record the missing stage with evidence, or correct the history." if fwd else "Correct the history or reopen the vendor properly."))

        # approval and go-live
        if st in ("active", "reassessment", "approved", "offboarding") or "active" in reached:
            appr = [h for h in hist if h["stage"] == "approved"]
            if not appr or not appr[0].get("approved_by"):
                issues.append(_i(_tier_sev(tier, "critical"), vid, nm, "GO_LIVE_WITHOUT_APPROVAL",
                                 "Vendor is or was live with no recorded approval and approver.", "Obtain and record retrospective approval."))
            missing = [c for c in cfg["approval_checklist"] if c != "approver_recorded" and not v["checklist"].get(c)]
            if v["data_types"] and set(v["data_types"]) & set(cfg["dpa_required_data"]) and not v["dpa_signed"]:
                missing.append("dpa_signed")
            if missing:
                issues.append(_i("high", vid, nm, "DUE_DILIGENCE_INCOMPLETE",
                                 f"Approved or live but missing: {', '.join(missing)}.", "Complete the missing due diligence items."))
        if st in ("active", "reassessment") and tier is None:
            issues.append(_i("high", vid, nm, "TIER_MISSING", "Live vendor has no risk tier.", "Tier the vendor."))

        # stalls
        limit = cfg["stall_days"].get(st)
        if limit is not None:
            days = (as_of - hist[-1]["date"]).days
            if days > limit:
                issues.append(_i("medium", vid, nm, "STALLED_STAGE", f"In {st} for {days} days (limit {limit}).", "Unblock or escalate."))

        # periodic reassessment
        if st in ("active", "reassessment"):
            if v["last_assessment"] is None:
                issues.append(_i(_tier_sev(tier), vid, nm, "REASSESSMENT_OVERDUE", "Live vendor has never been assessed.", "Run an assessment."))
            elif tier and add_months(v["last_assessment"], cfg["reassessment_months"][str(tier)]) < as_of:
                issues.append(_i(_tier_sev(tier), vid, nm, "REASSESSMENT_OVERDUE",
                                 f"Last assessed {v['last_assessment']}; Tier {tier} cadence is {cfg['reassessment_months'][str(tier)]} months.", "Run the periodic reassessment."))

        # offboarding
        if st in ("offboarding", "offboarded"):
            undone = [c for c in cfg["offboarding_checklist"] if not v["offboarding"].get(c)]
            if st == "offboarded" and undone:
                sev = "critical" if "access_revoked" in undone else "high"
                issues.append(_i(sev, vid, nm, "OFFBOARD_INCOMPLETE", f"Marked offboarded but not done: {', '.join(undone)}.", "Finish the offboarding checklist."))
            if st == "offboarding" and v["active_access"] and (as_of - hist[-1]["date"]).days > cfg["stall_days"]["offboarding"]:
                issues.append(_i("high", vid, nm, "OFFBOARD_ACCESS_LINGERING", "Offboarding for over the limit and the vendor still has access.", "Revoke access now."))
            if st == "offboarded" and v["active_access"]:
                issues.append(_i("critical", vid, nm, "OFFBOARD_ACCESS_LINGERING", "Offboarded vendor still has active access.", "Revoke access now."))

    issues.sort(key=lambda i: (SEV[i["severity"]], i["vendor"], i["check"]))
    return {"as_of": str(as_of), "issues": issues, "pipeline": pipeline}
