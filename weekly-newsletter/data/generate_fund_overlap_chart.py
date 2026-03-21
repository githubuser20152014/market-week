"""Generate the fund overlap chart for The Blueprint Issue #2.

Produces: site/assets/fund-overlap.png

Shows top-5 holdings (by portfolio weight %) for three "different" large-cap
growth funds side-by-side, making the overlap undeniable at a glance.
Fund names are generic (Fund A/B/C) — we illustrate the pattern, not any
specific real-world products.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

# ── Brand colours ──────────────────────────────────────────────────────────
NAVY   = "#1a2942"
GOLD   = "#c9a84c"
SLATE  = "#4a6080"
LIGHT  = "#f5f3ef"
MUTED  = "#8899aa"
TEAL   = "#3d7a8a"

# ── Data ───────────────────────────────────────────────────────────────────
# Three generic large-cap growth funds. Weights differ slightly so the bars
# aren't identical, but the overlap is obvious.
HOLDINGS = ["Apple", "Microsoft", "Nvidia", "Amazon", "Alphabet"]

FUND_A_WEIGHTS = [12.4, 11.1,  8.6,  5.2,  4.3]   # Large Cap Growth Fund
FUND_B_WEIGHTS = [11.8, 10.7,  9.2,  5.8,  4.9]   # Blue Chip Equity Fund
FUND_C_WEIGHTS = [13.1, 10.3,  7.9,  4.9,  5.1]   # Diversified Growth Fund

FUNDS = [
    ("Fund A\n(Large Cap Growth)", FUND_A_WEIGHTS, NAVY),
    ("Fund B\n(Blue Chip Equity)",  FUND_B_WEIGHTS, GOLD),
    ("Fund C\n(Diversified Growth)",FUND_C_WEIGHTS, TEAL),
]


def generate_chart(output_path=None):
    if output_path is None:
        here = Path(__file__).parent.parent
        output_path = here / "site" / "assets" / "fund-overlap.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_holdings = len(HOLDINGS)
    n_funds = len(FUNDS)
    x = np.arange(n_holdings)
    bar_width = 0.25
    offsets = [-(bar_width), 0, bar_width]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(LIGHT)
    ax.set_facecolor(LIGHT)

    # Grid
    ax.yaxis.grid(True, color="#d4cfc7", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d4cfc7")
    ax.spines["bottom"].set_color("#d4cfc7")

    # Bars
    for i, (label, weights, color) in enumerate(FUNDS):
        bars = ax.bar(
            x + offsets[i], weights, bar_width,
            label=label, color=color, zorder=3,
            alpha=0.88, edgecolor="white", linewidth=0.6
        )
        # Value labels on bars
        for bar, w in zip(bars, weights):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                f"{w:.1f}%",
                ha="center", va="bottom", fontsize=7.5, color=SLATE
            )

    # Axes
    ax.set_xticks(x)
    ax.set_xticklabels(HOLDINGS, fontsize=10, color=SLATE)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylim(0, 17)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_ylabel("% of fund assets", fontsize=10, color=SLATE, labelpad=8)

    # Title
    ax.set_title("Three funds. The same five companies.",
                 fontsize=13, fontweight="bold", color=NAVY, pad=14, loc="left")
    ax.text(0, 1.01,
            "Top-5 holdings by weight across three 'different' large-cap growth funds in a typical 401(k) menu",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)

    # Legend
    legend = ax.legend(loc="upper right", fontsize=8.5, frameon=True,
                       framealpha=0.9, edgecolor="#d4cfc7", ncol=3)
    legend.get_frame().set_facecolor(LIGHT)

    # Caption
    fig.text(0.01, -0.04,
             "Illustrative only. Fund names and weights are representative examples, not actual fund data.\n"
             "Real-world overlap varies by fund but the pattern is common in employer 401(k) menus.",
             fontsize=7.5, color=MUTED, linespacing=1.5)

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)
    print(f"Chart saved -> {output_path}")
    return output_path


if __name__ == "__main__":
    generate_chart()
