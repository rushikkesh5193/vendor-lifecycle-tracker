"""Synthetic vendors with lifecycle problems injected on purpose.

    python3 -m tools.gen_sample examples/sample_vendors.json
"""
import json
import sys

OK_CHECK = {"tier_assigned": True, "questionnaire_received": True, "evidence_reviewed": True}
OFF_DONE = {"access_revoked": True, "data_disposal_confirmed": True, "contract_closed": True, "register_updated": True}


def hist(*steps):
    return [{"stage": s, "date": d, **({"approved_by": a} if a else {})} for s, d, a in steps]


def clean_active(i, tier=3, data=("internal",)):
    return {"id": f"V{i:03d}", "name": f"Vendor {i:03d}", "tier": tier, "data_types": list(data), "stage": "active",
            "dpa_signed": True, "active_access": True, "last_assessment": "2026-06-15", "checklist": dict(OK_CHECK),
            "history": hist(("intake", "2025-01-02", None), ("due_diligence", "2025-01-10", None),
                            ("approved", "2025-02-20", "CISO"), ("active", "2025-03-01", None))}


def build():
    v = [clean_active(i) for i in range(11, 31)]
    # --- injected problems ---
    a = clean_active(1, tier=1, data=("financial",))
    a["history"] = hist(("intake", "2025-01-02", None), ("active", "2025-02-01", None))               # skipped due diligence and approval
    a["checklist"] = {}; a["dpa_signed"] = False; a["last_assessment"] = None
    b = clean_active(2, tier=2, data=("personal",))
    b["history"] = hist(("intake", "2025-01-02", None), ("due_diligence", "2025-01-10", None), ("approved", "2025-02-20", None), ("active", "2025-03-01", None))   # no approver
    c = clean_active(3, tier=3); c["last_assessment"] = "2024-06-01"                                  # 24-month cadence passed
    d = clean_active(4, tier=3); d["tier"] = None                                                       # live but untiered
    e = clean_active(5, tier=2)
    e.update(stage="due_diligence", history=hist(("intake", "2026-07-01", None), ("due_diligence", "2026-08-01", None)), checklist={}, last_assessment=None)   # 83 days in DD
    f = clean_active(6, tier=3)
    f.update(stage="offboarded", active_access=True, offboarding={"access_revoked": False, "data_disposal_confirmed": True, "contract_closed": True, "register_updated": True},
             history=hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"), ("active", "2024-03-01", None),
                          ("offboarding", "2026-08-01", None), ("offboarded", "2026-09-01", None)))   # access still live
    g = clean_active(7, tier=3)
    g.update(stage="offboarded", active_access=False, offboarding={"access_revoked": True, "data_disposal_confirmed": False, "contract_closed": True, "register_updated": True},
             history=hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"), ("active", "2024-03-01", None),
                          ("offboarding", "2026-08-01", None), ("offboarded", "2026-09-01", None)))   # data disposal not confirmed
    h = clean_active(8, tier=3)
    h.update(stage="offboarding", active_access=True, offboarding={},
             history=hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"), ("active", "2024-03-01", None),
                          ("offboarding", "2026-08-15", None)))   # 69 days, access still live
    i = clean_active(9, tier=3)
    i.update(stage="active", history=hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"),
                                          ("active", "2024-03-01", None), ("offboarding", "2025-06-01", None), ("offboarded", "2025-07-01", None), ("active", "2026-01-01", None)))   # offboarded vendor revived
    j = clean_active(10, tier=4); j["checklist"]["evidence_reviewed"] = False                          # approved without evidence review
    return {"_note": "Synthetic data. Problems are injected on purpose.", "vendors": [a, b, c, d, e, f, g, h, i, j] + v}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_vendors.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(build(), fh, indent=2)
        fh.write("\n")
