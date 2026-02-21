"""Generate a weekly price chart from index data."""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend

import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

# Color palette -- distinct, accessible colors for each asset
COLORS = {
    # US indices
    "S&P 500":      "#1f77b4",
    "Dow Jones":    "#ff7f0e",
    "Nasdaq":       "#2ca02c",
    "Russell 2000": "#d62728",
    "Gold":         "#FFD700",
    "10Y Treasury": "#9467bd",
    "USD Index":    "#17becf",
    # International indices
    "DAX":          "#1f77b4",
    "FTSE 100":     "#d62728",
    "CAC 40":       "#2ca02c",
    "Euro Stoxx 50":"#9467bd",
    "Nikkei 225":   "#ff7f0e",
    "Hang Seng":    "#17becf",
    "ASX 200":      "#e377c2",
    "MSCI EM":      "#bcbd22",
}


def generate_price_chart(raw_indices, date_str, output_dir, title=None):
    """Generate a normalized weekly performance chart.

    Instead of plotting raw prices (which span $4 to $44,000), we normalize
    each series to % change from first day's open. Uses a positional x-axis
    so only actual trading days appear -- no weekend gaps, and mixed-timezone
    datasets (e.g. APAC + EU) align cleanly.

    Args:
        raw_indices: Dict from fetch_index_data.
        date_str: Newsletter date string for the title.
        output_dir: Path to save the chart image.

    Returns:
        Path to the saved chart image.
    """
    # --- Build per-series data, filtering to weekdays only ---
    series = {}  # name -> {date_str: pct_change}
    all_dates = set()

    for name, info in raw_indices.items():
        data = info["data"]
        weekday_data = [
            d for d in data
            if datetime.strptime(d["date"], "%Y-%m-%d").weekday() < 5
        ]
        if len(weekday_data) < 2:
            continue
        base = weekday_data[0]["open"]
        pct_map = {
            d["date"]: ((d["close"] - base) / base) * 100
            for d in weekday_data
        }
        series[name] = pct_map
        all_dates.update(pct_map.keys())

    # Positional x-axis: cap to the 5 most recent trading days so that
    # indices with holiday gaps (e.g. Hang Seng during CNY) don't pull
    # the chart back into the prior week.
    sorted_dates = sorted(all_dates)[-5:]

    # Position 0 = synthetic "week open" at 0% for every series.
    # Positions 1..N = daily closes relative to that open.
    # This ensures all lines start at 0 on the left edge of the chart.
    pos = {d: i + 1 for i, d in enumerate(sorted_dates)}

    # Label position 0 with the weekday name of the first trading day
    first_day_label = (
        datetime.strptime(sorted_dates[0], "%Y-%m-%d").strftime("%a Open")
        if sorted_dates else "Open"
    )
    x_labels = [first_day_label] + [
        datetime.strptime(d, "%Y-%m-%d").strftime("%b %d")
        for d in sorted_dates
    ]
    x_ticks = list(range(len(sorted_dates) + 1))

    fig, ax = plt.subplots(figsize=(10, 5))

    for name, pct_map in series.items():
        xs = [0] + [pos[d] for d in sorted_dates if d in pct_map]
        ys = [0.0] + [pct_map[d] for d in sorted_dates if d in pct_map]
        color = COLORS.get(name, "#8c564b")
        ax.plot(xs, ys, marker="o", linewidth=2, label=name,
                color=color, markersize=5)

    # Formatting
    chart_title = title or "Framework Foundry Weekly -- Performance (% Change from Monday Open)"
    ax.set_title(chart_title, fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("% Change", fontsize=11)
    ax.set_xlabel("")
    ax.axhline(y=0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)

    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, ha="center")

    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    # Save
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    chart_path = output_dir / f"chart_{date_str}.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)

    return chart_path
