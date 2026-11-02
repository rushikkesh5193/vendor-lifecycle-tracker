from datetime import date

from vlt import analyse, load_config, validate

AS_OF = date(2026, 10, 23)
CFG = load_config()


def vendor(**kw):
    d = {"id": "T1", "name": "Test", "tier": 3, "data_types": ["internal"], "stage": "active", "dpa_signed": True,
         "active_access": True, "last_assessment": "2026-06-15",
         "checklist": {"tier_assigned": True, "questionnaire_received": True, "evidence_reviewed": True},
         "history": [{"stage": "intake", "date": "2025-01-02"}, {"stage": "due_diligence", "date": "2025-01-10"},
                     {"stage": "approved", "date": "2025-02-20", "approved_by": "CISO"}, {"stage": "active", "date": "2025-03-01"}]}
    d.update(kw)
    return d


def hist(*steps):
    return [{"stage": s, "date": dt, **({"approved_by": a} if a else {})} for s, dt, a in steps]


def run(**kw):
    return analyse(validate([vendor(**kw)]), CFG, AS_OF)


def checks(**kw):
    return {i["check"] for i in run(**kw)["issues"]}
