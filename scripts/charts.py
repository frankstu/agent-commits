"""Diagramme aus results/counts.jsonl.

    .venv/bin/python scripts/charts.py [Blog-Repo]

Schreibt results/monthly.json und results/summary.md; mit Blog-Repo zusätzlich:
  static/img/engpass-freigabe/commits-dunkel.png          Querformat, Artikel und Vorschaubild
  static/img/engpass-freigabe/karte-dunkel.png            Hochformat 4:5, Startseitenkarte
  linkedin/img/engpass-freigabe/linkedin-hochformat.png   Hochformat 4:5, hell

Je Monat zählt der Mittelwert der Durchgänge; die Spanne steht in monthly.json.
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  # pylint: disable=wrong-import-position
from matplotlib.ticker import FuncFormatter  # noqa: E402  # pylint: disable=wrong-import-position
from PIL import Image  # noqa: E402  # pylint: disable=wrong-import-position

ROOT = Path(__file__).resolve().parents[1]
DPI = 180
MONTHS_DE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
THEMES = {
    "hell": {"ACCENT": "#2a78d6", "DEEMPH": "#c9c7c0", "SURFACE": "#fcfcfb", "INK": "#0b0b0b",
             "INK_2": "#52514e", "MUTED": "#898781", "RULE": "#e2e1dc"},
    "dunkel": {"ACCENT": "#f2c037", "DEEMPH": "#4a4a52", "SURFACE": "#121214", "INK": "#f4f4f5",
               "INK_2": "#b4b4bb", "MUTED": "#8a8a93", "RULE": "#2a2a2f"},
}


def load() -> dict[str, list[dict[str, object]]]:
    values: dict[tuple[str, str], list[int]] = defaultdict(list)
    meta: dict[tuple[str, str], dict[str, object]] = {}
    for line in (ROOT / "results" / "counts.jsonl").read_text().splitlines():
        r = json.loads(line)
        key = (r["query"], r["month"])
        values[key].append(int(r["total_count"]))
        meta[key] = {"start": r["start"], "end": r["end"]}
    out: dict[str, list[dict[str, object]]] = defaultdict(list)
    for (query, month), vals in sorted(values.items()):
        out[query].append({"month": month, **meta[(query, month)], "values": vals,
                           "mean": round(statistics.mean(vals)), "min": min(vals),
                           "max": max(vals)})
    (ROOT / "results" / "monthly.json").write_text(json.dumps(out, indent=2))
    return out


def de(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


def label(month: str) -> str:
    year, m = month.split("-")
    return f"{MONTHS_DE[int(m) - 1]}\n{year}" if m in ("01", "07") else MONTHS_DE[int(m) - 1]


def summary(data: dict[str, list[dict[str, object]]]) -> None:
    lines = ["| Monat | Claude als Co-Autor (Mittel) | Spanne | „fix“ (Mittel) |",
             "|---|---|---|---|"]
    fix = {str(r["month"]): r for r in data.get("fix", [])}
    for r in data["claude"]:
        f = fix.get(str(r["month"]))
        lines.append(f"| {r['month']} | {de(float(r['mean']))} | {de(float(r['min']))}–"  # type: ignore
                     f"{de(float(r['max']))} | {de(float(f['mean'])) if f else '–'} |")  # type: ignore
    (ROOT / "results" / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def _bars(ax, rows: list[dict[str, object]], c: dict[str, str], portrait: bool) -> None:
    ax.set_facecolor(c["SURFACE"])
    xs = list(range(len(rows)))
    ys = [float(r["mean"]) for r in rows]  # type: ignore
    colors = [c["ACCENT"] if str(r["month"]) == "2026-09" else
              (c["INK_2"] if str(r["month"]) == "2025-09" else c["DEEMPH"]) for r in rows]
    ax.bar(xs, ys, color=colors, width=0.72)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(c["RULE"])
    ax.tick_params(colors=c["MUTED"], labelsize=12 if portrait else 10.5, length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:.0f} Mio." if v else "0"))
    ax.grid(axis="y", color=c["RULE"], lw=0.8)
    ax.set_axisbelow(True)
    step = 3 if portrait else 1
    ax.set_xticks(xs[::step], [label(str(r["month"])) for r in rows][::step])
    for i, r in enumerate(rows):
        if str(r["month"]) in ("2025-09", "2026-09"):
            v = float(r["mean"])  # type: ignore
            text = (f"{v / 1e6:.1f}".replace(".", ",") + " Mio.") if v >= 1e6 else de(round(v, -4))
            ax.text(i, v, text, ha="center", va="bottom", fontsize=13 if portrait else 11.5,
                    fontweight="bold",
                    color=c["ACCENT"] if str(r["month"]) == "2026-09" else c["INK_2"])


def chart(data: dict[str, list[dict[str, object]]], theme: str, path: Path,
          portrait: bool) -> None:
    c = THEMES[theme]
    plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "Arial", "sans-serif"]})
    rows = [r for r in data["claude"] if str(r["month"]) <= "2026-09"]  # Oktober unvollständig
    fig = plt.figure(figsize=(8, 10) if portrait else (12, 6.6), dpi=DPI, facecolor=c["SURFACE"])
    left = 0.07 if portrait else 0.05
    foot = ("Commit-Suche von GitHub nach „Co-Authored-By: Claude“ in öffentlichen Repositories, "
            "abgefragt am 22.10.2026 · Schätzwerte der Suche,\nfür 2026 eher Untergrenze · "
            "Claude Code setzt die Zeile standardmäßig · Daten und Code: "
            "github.com/frankstu/agent-commits")
    if portrait:
        fig.text(left, 0.95, "EIGENE ZÄHLUNG · GITHUB", fontsize=15, color=c["ACCENT"],
                 fontweight="bold", va="top")
        fig.text(left, 0.915, "Commits mit Claude\nals Co-Autor", fontsize=44,
                 fontweight="bold", color=c["INK"], va="top", linespacing=1.05)
        fig.text(left, 0.77, "An einem Dienstag im September", fontsize=17, color=c["INK_2"],
                 va="top")
        fig.text(left, 0.725, "2025", fontsize=17, color=c["MUTED"], va="top")
        fig.text(left, 0.70, "18.100", fontsize=44, color=c["INK_2"], va="top",
                 fontweight="bold")
        fig.text(0.52, 0.725, "2026", fontsize=17, color=c["MUTED"], va="top")
        fig.text(0.52, 0.70, "> 900.000", fontsize=44, color=c["ACCENT"], va="top",
                 fontweight="bold")
        fig.text(left, 0.585, "Je Monat, Januar 2025 bis September 2026", fontsize=15,
                 color=c["INK_2"], va="top")
        ax = fig.add_axes((left + 0.07, 0.16, 0.82, 0.39))
        foot = ("GitHub-Suche nach „Co-Authored-By: Claude“ in öffentlichen Repositories,\n"
                "abgefragt am 22.10.2026 · Schätzwerte, für 2026 eher Untergrenze\n"
                "Daten und Code: github.com/frankstu/agent-commits")
    else:
        fig.text(left, 0.94, "Öffentliche Commits mit Claude als Co-Autor", fontsize=22,
                 fontweight="bold", color=c["INK"], va="top")
        fig.text(left, 0.865, "Je Monat auf GitHub, Januar 2025 bis September 2026 · "
                 "für 2026 Mittel aus zwei Abfragen", fontsize=12.5, color=c["INK_2"], va="top")
        ax = fig.add_axes((left + 0.04, 0.17, 0.88, 0.6))
    _bars(ax, rows, c, portrait)
    fig.text(left, 0.03, foot, fontsize=9.5 if not portrait else 10.5, color=c["MUTED"],
             va="bottom", linespacing=1.35)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, facecolor=c["SURFACE"])
    plt.close(fig)
    if portrait:
        with Image.open(path) as image:
            small = image.convert("RGB").resize((1080, 1350), Image.Resampling.LANCZOS)
            small.quantize(colors=128).save(path, optimize=True)


def main() -> None:
    data = load()
    summary(data)
    if len(sys.argv) > 1:
        blog = Path(sys.argv[1])
        chart(data, "dunkel", blog / "static/img/engpass-freigabe/commits-dunkel.png", False)
        chart(data, "dunkel", blog / "static/img/engpass-freigabe/karte-dunkel.png", True)
        chart(data, "hell", blog / "linkedin/img/engpass-freigabe/linkedin-hochformat.png", True)


if __name__ == "__main__":
    main()
