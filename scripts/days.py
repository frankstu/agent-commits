"""Tageswerte und Stichprobe zur Kontrolle der Monatswerte (results/days.jsonl).

Fragt für einzelne Tage die Commit-Suche ab und wertet für einen Tag die ersten 100 Treffer aus:
Enthält die Nachricht die Co-Autor-Zeile, aus wie vielen Repositories stammen sie, welches Modell
steht in der Zeile. Gespeichert werden nur Summen, keine Commits oder Personen.

    python3 scripts/days.py 2025-09-16 2026-09-08 2026-09-15 --sample 2026-09-15
"""

import argparse
import collections
import json
import re
import subprocess
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERY = '"Co-Authored-By: Claude"'
TRAILER = re.compile(r"(?im)^co-authored-by:\s*(claude[^<\n]*)")


def search(day: str, per_page: int) -> dict[str, object]:
    res = subprocess.run(["gh", "api", "-X", "GET", "search/commits", "-f",
                          f"q={QUERY} committer-date:{day}..{day}", "-f", f"per_page={per_page}"],
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("days", nargs="+")
    parser.add_argument("--sample")
    args = parser.parse_args()
    out = []
    for day in args.days:
        sample = day == args.sample
        data = search(day, 100 if sample else 1)
        rec: dict[str, object] = {
            "query": QUERY, "day": day,
            "weekday": date.fromisoformat(day).strftime("%A"),
            "total_count": data["total_count"], "incomplete": data["incomplete_results"],
            "at": time.strftime("%Y-%m-%d")}
        if sample:
            items = data["items"]
            assert isinstance(items, list)
            names = collections.Counter(m.group(1).strip() for i in items
                                        if (m := TRAILER.search(i["commit"]["message"])))
            rec["sample"] = {"items": len(items), "with_trailer_line": sum(names.values()),
                             "repositories": len({i["repository"]["full_name"] for i in items}),
                             "models": dict(names.most_common())}
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False))
        time.sleep(35)
    (ROOT / "results" / "days-neu.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")


if __name__ == "__main__":
    main()
