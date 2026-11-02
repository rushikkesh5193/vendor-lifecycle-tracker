"""Lifecycle model, input loading and validation."""
import calendar
import json
from datetime import date

STAGES = ("intake", "due_diligence", "approved", "active", "reassessment", "offboarding", "offboarded", "rejected")
ORDER = {"intake": 0, "due_diligence": 1, "approved": 2, "active": 3, "reassessment": 4, "offboarding": 5, "offboarded": 6}
ALLOWED = {
    "intake": ["due_diligence"],
    "due_diligence": ["approved", "rejected"],
    "approved": ["active"],
    "active": ["reassessment", "offboarding"],
    "reassessment": ["active", "offboarding"],
    "offboarding": ["offboarded"],
    "offboarded": [],
    "rejected": [],
}
SEVERITIES = ("critical", "high", "medium", "low")
DATA_TYPES = ("none", "internal", "personal", "financial", "sensitive", "health")


def parse_date(s, field="date"):
    if s in (None, ""):
        return None
    try:
        y, m, d = (int(x) for x in str(s).split("-"))
        return date(y, m, d)
    except (ValueError, TypeError):
        raise ValueError(f"{field}: expected YYYY-MM-DD, got {s!r}")


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def load(path):
    with open(path, encoding="utf-8") as f:
        return validate(json.load(f))


def validate(data):
    rows = data["vendors"] if isinstance(data, dict) else data
    out, seen = [], set()
    for v in rows:
        for k in ("id", "name", "stage", "history"):
            if k not in v:
                raise ValueError(f"vendor {v.get('id', '?')}: missing {k}")
        if v["id"] in seen:
            raise ValueError(f"duplicate vendor id {v['id']}")
        seen.add(v["id"])
        if v["stage"] not in STAGES:
            raise ValueError(f"vendor {v['id']}: unknown stage {v['stage']!r}")
        tier = v.get("tier")
        if tier is not None and tier not in (1, 2, 3, 4):
            raise ValueError(f"vendor {v['id']}: tier must be 1..4 or null, got {tier!r}")
        for d in v.get("data_types", []):
            if d not in DATA_TYPES:
                raise ValueError(f"vendor {v['id']}: unknown data type {d!r}")
        q = dict(v)
        q["tier"] = tier
        q["data_types"] = list(v.get("data_types", []))
        hist, prev = [], None
        for h in v["history"]:
            if h["stage"] not in STAGES:
                raise ValueError(f"vendor {v['id']}: history has unknown stage {h['stage']!r}")
            dt = parse_date(h.get("date"), f"vendor {v['id']} history date")
            if dt is None:
                raise ValueError(f"vendor {v['id']}: history entry without a date")
            if prev and dt < prev:
                raise ValueError(f"vendor {v['id']}: history dates go backwards")
            prev = dt
            hist.append({"stage": h["stage"], "date": dt, "approved_by": h.get("approved_by")})
        if not hist or hist[-1]["stage"] != v["stage"]:
            raise ValueError(f"vendor {v['id']}: history must end at the current stage ({v['stage']})")
        q["history"] = hist
        q["last_assessment"] = parse_date(v.get("last_assessment"), f"vendor {v['id']}.last_assessment")
        q["checklist"] = dict(v.get("checklist", {}))
        q["offboarding"] = dict(v.get("offboarding", {}))
        q["dpa_signed"] = bool(v.get("dpa_signed", False))
        q["active_access"] = bool(v.get("active_access", False))
        out.append(q)
    return out
