"""Öffentliche GitHub-Commits je Monat zählen, die einen KI-Agenten als Co-Autor nennen.

Nutzt die Commit-Suche der GitHub-API über `gh api` (angemeldet). Die Suche liefert Schätzwerte
(`incomplete_results`), deshalb zählt das Skript die Monate 2026 ein zweites Mal. Langsam
getaktet wegen des sekundären Rate-Limits der Suche.

    python3 scripts/count.py   # schreibt results/counts.jsonl, ergänzt fehlende Einträge
"""

import json
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "counts.jsonl"

QUERIES = {
    "claude": '"Co-Authored-By: Claude"',
    "fix": "fix",  # grobe Vergleichsgröße für das allgemeine Commit-Volumen
}
FIRST = date(2025, 1, 1)
LAST = date(2026, 10, 21)  # Stichtag der Messung
PAUSE = 30.0


def months() -> list[tuple[str, date, date]]:
    out = []
    d = FIRST
    while d <= LAST:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        end = min(nxt - timedelta(days=1), LAST)
        out.append((d.strftime("%Y-%m"), d, end))
        d = nxt
    return out


def count(query: str, start: date, end: date) -> tuple[int, bool]:
    q = f"{query} committer-date:{start.isoformat()}..{end.isoformat()}"
    for attempt in range(6):
        res = subprocess.run(["gh", "api", "-X", "GET", "search/commits", "-f", f"q={q}",
                              "-f", "per_page=1", "--jq", "[.total_count, .incomplete_results]"],
                             capture_output=True, text=True, check=False)
        if res.returncode == 0:
            total, incomplete = json.loads(res.stdout)
            return int(total), bool(incomplete)
        wait = 60 * (attempt + 1)
        print(f"  Fehler ({res.stderr.strip()[:80]}), warte {wait} s", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"keine Antwort für {q}")


# Plan: Claude für alle Monate, zweiter Durchgang nur 2026 (Schwankung), Vergleichsgröße „fix“
# nur an Stichmonaten. Mehr lässt das sekundäre Rate-Limit der Suche in vertretbarer Zeit nicht zu.
FIX_MONTHS = ("2025-01", "2025-07", "2026-01", "2026-09")


def plan() -> list[tuple[str, str, date, date, int]]:
    jobs = []
    for month, start, end in months():
        jobs.append(("claude", QUERIES["claude"], start, end, 1))
    for month, start, end in months():
        if month.startswith("2026"):
            jobs.append(("claude", QUERIES["claude"], start, end, 2))
    for month, start, end in months():
        if month in FIX_MONTHS:
            jobs.append(("fix", QUERIES["fix"], start, end, 1))
    return jobs


def main() -> None:
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            r = json.loads(line)
            done.add((r["query"], r["month"], r["pass"]))
    with OUT.open("a") as handle:
        for key, query, start, end, p in plan():
            month = start.strftime("%Y-%m")
            if (key, month, p) in done:
                continue
            total, incomplete = count(query, start, end)
            rec = {"query": key, "q": query, "month": month, "start": start.isoformat(),
                   "end": end.isoformat(), "pass": p, "total_count": total,
                   "incomplete": incomplete, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            handle.write(json.dumps(rec) + "\n")
            handle.flush()
            print(key, month, p, total, "unvollständig" if incomplete else "", flush=True)
            time.sleep(PAUSE)


if __name__ == "__main__":
    main()
