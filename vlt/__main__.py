import argparse
import sys
from datetime import date
from pathlib import Path

from . import analyse, load, load_config, parse_date
from .models import SEVERITIES
from .report import issues_csv, to_json, to_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vlt", description="Vendor lifecycle gate checks.")
    ap.add_argument("input")
    ap.add_argument("--as-of")
    ap.add_argument("--out-dir")
    ap.add_argument("--config")
    ap.add_argument("--fail-on", choices=SEVERITIES)
    a = ap.parse_args(argv)
    try:
        as_of = parse_date(a.as_of, "--as-of") if a.as_of else date.today()
        vendors = load(a.input)
        res = analyse(vendors, load_config(a.config), as_of)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    md = to_markdown(res, vendors)
    if a.out_dir:
        d = Path(a.out_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "report.md").write_text(md, encoding="utf-8")
        (d / "report.json").write_text(to_json(res), encoding="utf-8")
        (d / "issues.csv").write_text(issues_csv(res), encoding="utf-8")
        print(f"{len(res['issues'])} issues -> {d}/")
    else:
        print(md)
    if a.fail_on and any(SEVERITIES.index(i["severity"]) <= SEVERITIES.index(a.fail_on) for i in res["issues"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
