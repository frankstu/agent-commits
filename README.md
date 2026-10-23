# Agent Commits

> **English summary.** How many public GitHub commits name Claude as co-author? Claude Code adds a
> `Co-Authored-By: Claude …` trailer to every commit by default. On 22 October 2026 I counted, per
> month from January 2025 to October 2026, the public commits whose message contains
> `"Co-Authored-By: Claude"`, using GitHub's commit search API. September 2025: about 460,000;
> September 2026: 14.2 to 15.3 million (two queries), roughly 30×. Single-day queries are more
> reliable: Tuesday 16 Sep 2025: 18,100 (complete); Tuesdays 8 and 15 Sep 2026: about 925,000 and
> 953,000 (incomplete, so lower bounds). A sample of 100 hits from 15 Sep 2026 all contained the
> trailer (70 repositories). GitHub's search returns estimates (`incomplete_results`), so read the
> numbers as order of magnitude. Write-up (German):
> [frankstuch.de/artikel/engpass-freigabe](https://frankstuch.de/artikel/engpass-freigabe/).
> The rest of this README is in German.

Wie viele öffentliche Commits auf GitHub nennen Claude als Co-Autor? Claude Code schreibt
standardmäßig die Zeile `Co-Authored-By: <Modell> <noreply@anthropic.com>` in jeden Commit
(Einstellung `attribution.commit`, abschaltbar).

## Ergebnisse

- [`results/summary.md`](results/summary.md): Monatswerte, für 2026 Mittel und Spanne aus zwei Abfragen
- [`results/counts.jsonl`](results/counts.jsonl): jede einzelne Abfrage mit Zeitpunkt und `incomplete`
- [`results/days.jsonl`](results/days.jsonl): Tageswerte zur Kontrolle und die Stichprobe

## Aufruf

    gh auth login                      # die Commit-Suche braucht eine Anmeldung
    python3 scripts/count.py           # langsam: etwa eine Abfrage pro halbe Minute
    python3 -m pip install matplotlib pillow
    python3 scripts/charts.py [Pfad zum Blog-Repo]

## Grenzen

- Die Commit-Suche liefert Schätzwerte. Fast alle Abfragen meldeten `incomplete_results`; zwei
  Abfragen desselben Monats lagen bis zu 30 % auseinander. Tageswerte lagen 2026 rund doppelt so
  hoch wie die Monatswerte pro Tag, die Monatswerte für 2026 sind daher eher Untergrenzen.
- Nur öffentliche Repositories, nur Commits mit der Zeile. Wer sie abschaltet oder andere
  Werkzeuge nutzt, fehlt; Werkzeuge werden deshalb nicht verglichen.
- „fix“ als Vergleichsgröße für das allgemeine Wachstum ist grob und enthält selbst Agenten-Commits.
- Die Tageswerte in `days.jsonl` stammen aus Einzelabfragen am 22.10.2026 mit derselben Suche wie `scripts/days.py`; das Skript schreibt neue Läufe nach `days-neu.jsonl`. Die Stichprobe sind die ersten 100 Treffer, keine Zufallsauswahl.

## Lizenz

MIT
