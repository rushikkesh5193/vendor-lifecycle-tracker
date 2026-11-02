import csv
import io
import json

from .models import STAGES


def issues_csv(res):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(["severity", "vendor", "name", "check", "detail", "action"])
    w.writerows([[i["severity"], i["vendor"], i["name"], i["check"], i["detail"], i["action"]] for i in res["issues"]])
    return b.getvalue()


def to_json(res):
    return json.dumps(res, indent=2)


def to_markdown(res, vendors):
    L = ["# Vendor lifecycle report", "", f"As of {res['as_of']}. {len(vendors)} vendors, {len(res['issues'])} issues.", "", "## Pipeline", "",
         "| Stage | Vendors |", "|---|---|"]
    L += [f"| {s} | {res['pipeline'][s]} |" for s in STAGES if s in res["pipeline"]]
    L += ["", "## Issues", ""]
    for sev in ("critical", "high", "medium", "low"):
        rows = [i for i in res["issues"] if i["severity"] == sev]
        if rows:
            L += [f"### {sev.title()} ({len(rows)})", ""]
            L += [f"- **{i['check']}** {i['name']} (`{i['vendor']}`): {i['detail']} *Action:* {i['action']}" for i in rows] + [""]
    return "\n".join(L) + "\n"
