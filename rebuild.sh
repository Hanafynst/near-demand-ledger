#!/bin/bash
# One command that rebuilds every chart from raw data.
set -e
cd "$(dirname "$0")"
python3 scripts/fetch_nearblocks.py
python3 scripts/fetch_rpc.py
python3 scripts/fetch_defillama.py
python3 scripts/analyze.py
python3 scripts/build_charts.py
echo "Done. Open dashboard/index.html"
