"""Record ticket evidence without performing any Git operation."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re

from criclytics_app.paths import PROJECT_ROOT


def record(ticket_id, status, evidence):
    candidates = list((PROJECT_ROOT / "tickets").glob(ticket_id.lower() + "-*.md"))
    if len(candidates) != 1:
        raise ValueError("Expected exactly one ticket file")
    path = candidates[0]
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^- Status: .*$", "- Status: " + status, text, count=1, flags=re.M)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    text += "\n### Session update " + stamp + "\n\n" + evidence + "\n"
    path.write_text(text, encoding="utf-8")
    index = PROJECT_ROOT / "tickets.md"
    rows = index.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(rows):
        if line.startswith("| [" + ticket_id.upper() + "]"):
            cells = line.split("|")
            cells[-2] = " " + status + " "
            rows[i] = "|".join(cells)
    index.write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticket")
    parser.add_argument("status")
    parser.add_argument("evidence")
    args = parser.parse_args()
    record(args.ticket, args.status, args.evidence)
