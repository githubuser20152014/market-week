"""Generate the asset allocation growth curve chart for the Investing 101 article.

Produces: site/assets/asset-allocation-growth.png

Two lines diverging from $200,000 over 17 years:
  - 70% stocks / 30% bonds  @ ~7% annualized
  - 40% stocks / 60% bonds  @ ~5% annualized
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ── Brand colours ──────────────────────────────────────────────────────────
NAVY   = "#1a2942"
GOLD   = "#c9a84c"
SLATE  = "#4a6080"
LIGHT  = "#f5f3ef"
MUTED  = "#8899aa"
WHITE  = "#ffffff"

def generate_chart(output_path=None):
    if output_path is None:
        here = Path(__file__).parent.parent
        output_path = here / "site" / "assets" / "asset-allocation-growth.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Data ───────────────────────────────────────────────────────────────
    start   = 200_000
    years   = list(range(0, 18))          # 0 → 17
    rate_a  = 0.07                        # 70/30 portfolio
    rate_b  = 0.05                        # 40/60 portfolio

    values_a = [start * (1 + rate_a) ** y for y in years]
    values_b = [start * (1 + rate_b) ** y for y in years]

    # ── Figure ─────────────────────────────────────────────────────────────
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

    # Lines
    ax.plot(years, values_a, color=NAVY,  linewidth=2.5, label="70% stocks / 30% bonds  (~7% avg return)", zorder=3)
    ax.plot(years, values_b, color=GOLD,  linewidth=2.5, label="40% stocks / 60% bonds  (~5% avg return)", zorder=3)

    # End-point labels
    end_a = values_a[-1]
    end_b = values_b[-1]
    ax.annotate(f"${end_a/1_000:.0f}K",
                xy=(17, end_a), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.annotate(f"${end_b/1_000:.0f}K",
                xy=(17, end_b), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=10, fontweight="bold", color="#9a7a2e")

    # Gap annotation at year 17
    mid_y = (end_a + end_b) / 2
    ax.annotate("", xy=(16.5, end_a), xytext=(16.5, end_b),
                arrowprops=dict(arrowstyle="<->", color=SLATE, lw=1.2))
    ax.text(14.6, mid_y, f"+${(end_a - end_b)/1_000:.0f}K difference",
            fontsize=9, color=SLATE, va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc=LIGHT, ec="#d4cfc7", lw=0.8))

    # Starting point marker
    ax.plot(0, start, "o", color=MUTED, markersize=5, zorder=4)
    ax.text(0.2, start - 18_000, "Both start\nat $200K",
            fontsize=8, color=MUTED, va="top", linespacing=1.4)

    # Axes
    ax.set_xlim(-0.5, 19)
    ax.set_ylim(100_000, 800_000)
    ax.set_xlabel("Years invested", fontsize=10, color=SLATE, labelpad=8)
    ax.set_ylabel("Portfolio value", fontsize=10, color=SLATE, labelpad=8)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(1))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1_000:.0f}K"))
    ax.tick_params(colors=MUTED, labelsize=9)

    # Title
    ax.set_title("Same starting point. Very different finish.",
                 fontsize=13, fontweight="bold", color=NAVY, pad=14, loc="left")
    ax.text(0, 1.01,
            "Same $200,000 invested over 17 years — the only difference is the stock/bond ratio",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)

    # Legend
    legend = ax.legend(loc="upper left", fontsize=9, frameon=True,
                       framealpha=0.9, edgecolor="#d4cfc7")
    legend.get_frame().set_facecolor(LIGHT)

    # Caption
    fig.text(0.01, -0.04,
             "Illustrative only. Based on historical average annualised returns: ~7% for a 70/30 and ~5% for a 40/60 portfolio.\n"
             "Past performance does not guarantee future results.",
             fontsize=7.5, color=MUTED, linespacing=1.5)

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)
    print(f"Chart saved -> {output_path}")
    return output_path


if __name__ == "__main__":
    generate_chart()
