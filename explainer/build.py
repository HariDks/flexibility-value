"""Inject the model layer into the screener page.

The page is a template with a `/*DATA*/` marker. Keeping the data out of the
HTML source means the numbers always come from a fresh `build_screener.py` run
rather than from something pasted in and left to rot.

    python src/build_screener.py --verify && python explainer/build.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "processed" / "screener-data.json"
if not DATA.exists():
    DATA = HERE / "screener-data.json"

raw = json.loads(DATA.read_text())
# Only the two markets the chart draws need week profiles; the screener itself
# needs every run, and those are small.
raw["weeks"] = {k: v for k, v in raw["weeks"].items() if k in ("sa", "miso")}

out = (HERE / "screener.template.html").read_text().replace(
    "/*DATA*/", json.dumps(raw, separators=(",", ":")))
(HERE / "screener.html").write_text(out)
print(f"explainer/screener.html  {len(out) / 1024:.0f} KB")
