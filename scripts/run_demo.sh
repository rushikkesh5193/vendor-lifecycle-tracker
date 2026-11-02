#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m tools.gen_sample examples/sample_vendors.json
python3 -m vlt examples/sample_vendors.json --as-of 2026-10-23 --out-dir examples
python3 -m unittest discover -s tests
