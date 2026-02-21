"""Generate a weekly price chart from index data."""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path

# Color palette -- distinct, accessible colors for each asset
COLORS = {
    "S&P 500": "#1f77b4",
    "Dow Jones": "#ff7f0e",
    "Nasdaq": "#2ca02c",
    "Russell 2000": "#d62728",
    "Gold": "#FFD700",
    "10Y Treasury": "#9467bd",
    "USD Index": "#17becf",
}

DEFAULT_COLOR = "#8c564b"


def generate_price_chart(raw_indices, date_str, output_dir):
    """Generate a normalized weekly performance chart.

    Instead of plotting raw prices (which span $4 to $44,000), we normalize
    each series to % change from Monday's open. This makes all assets
    comparable on a single axis.

    Args:
        raw_indices: Dict from fetch_index_data.
        date_str: Newsletter date string for the title.
        output_dir: Path to save the chart image.

    Returns:
        Path to the saved chart image.
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    for name, info in raw_indices.items():
        data = info["data"]
        if len(data) < 2:
            continue

        # Filter to weekdays only (Mon-Fri)
        weekday_data = [
            d for d in data
            if datetime.strptime(d["date"], "%Y-%m-%d").weekday() < 5
        ]
        if len(weekday_data) < 2:
            continue

        dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in weekday_data]
        base = weekday_data[0]["open"]
        pct_changes = [((d["close"] - base) / base) * 100 for d in weekday_data]

        color = COLORS.get(name, DEFAULT_COLOR)
        ax.plot(dates, pct_changes, marker="o", linewidth=2, label=name,
                color=color, markersize=5)

    # Formatting
    ax.set_title(f"Framework Foundry Weekly -- Performance (% Change from Monday Open)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("% Change", fontsize=11)
    ax.set_xlabel("")
    ax.axhline(y=0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=(0, 1, 2, 3, 4)))
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Style tweaks
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
