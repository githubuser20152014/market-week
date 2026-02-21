"""Process raw data into newsletter-ready content."""


def process_index_data(raw):
    """Compute weekly performance for each index.

    Args:
        raw: Dict from fetch_index_data, keyed by index name.

    Returns:
        List of dicts sorted by weekly_pct (best to worst), each with:
        name, symbol, close, weekly_pct, week_high, week_low
    """
    results = []
    for name, info in raw.items():
        data = info["data"]
        if len(data) < 2:
            continue
        first_open = data[0]["open"]
        last_close = data[-1]["close"]
        weekly_pct = ((last_close - first_open) / first_open) * 100

        week_high = max(d["high"] for d in data)
        week_low = min(d["low"] for d in data)

        results.append({
            "name": name,
            "symbol": info["symbol"],
            "close": last_close,
            "weekly_pct": round(weekly_pct, 2),
            "week_high": week_high,
            "week_low": week_low,
        })

    results.sort(key=lambda x: x["weekly_pct"], reverse=True)
    return results


def generate_narrative(index_data, econ):
    """Generate a top-of-newsletter narrative summarizing the week.

    Reads the index performance and economic events to produce a
    2-3 paragraph plain-English summary an investor can scan quickly.
    """
    if not index_data:
        return "Markets were closed this week."

    best = index_data[0]
    worst = index_data[-1]

    # Count how many indices were positive vs negative
    up_count = sum(1 for i in index_data if i["weekly_pct"] > 0)
    down_count = len(index_data) - up_count

    # Find gold, treasury, and USD specifically
    gold = next((i for i in index_data if i["name"] == "Gold"), None)
    treasury = next((i for i in index_data if "Treasury" in i["name"]), None)
    usd = next((i for i in index_data if i["name"] == "USD Index"), None)

    # Build the opening paragraph about overall market direction
    if up_count == len(index_data):
        tone = "Markets rallied across the board this week"
    elif down_count == len(index_data):
        tone = "It was a rough week across the board"
    elif up_count > down_count:
        tone = "Most markets posted gains this week"
    else:
        tone = "Markets were mixed this week"

    para1 = (
        f"{tone}, with {best['name']} leading at {best['weekly_pct']:+.2f}% "
        f"and {worst['name']} lagging at {worst['weekly_pct']:+.2f}%."
    )

    # Add color on gold and treasuries if present
    safe_haven_notes = []
    if gold:
        direction = "climbing" if gold["weekly_pct"] > 0 else "slipping"
        safe_haven_notes.append(
            f"Gold {direction} {abs(gold['weekly_pct']):.2f}% to ${gold['close']:,.2f}"
        )
    if treasury:
        direction = "rising" if treasury["weekly_pct"] > 0 else "falling"
        safe_haven_notes.append(
            f"the 10-year yield {direction} to {treasury['close']:.2f}%"
        )

    if usd:
        direction = "strengthening" if usd["weekly_pct"] > 0 else "weakening"
        safe_haven_notes.append(
            f"the dollar {direction} {abs(usd['weekly_pct']):.2f}% to {usd['close']:.2f}"
        )

    if safe_haven_notes:
        para1 += " On the safe-haven front, " + " while ".join(safe_haven_notes) + "."

    # Build second paragraph about key economic drivers
    past = econ.get("past_week", [])
    surprises = [e for e in past if e.get("surprise") in ("above", "below")]

    if surprises:
        drivers = []
        for e in surprises:
            name = e["event"]
            if e["surprise"] == "above":
                drivers.append(f"{name} came in above expectations ({e['actual']}{e['unit']} vs. {e['expected']}{e['unit']})")
            else:
                drivers.append(f"{name} came in below expectations ({e['actual']}{e.get('unit', '')} vs. {e['expected']}{e.get('unit', '')})")

        para2 = "The macro picture was busy. " + ". ".join(drivers) + "."
        # Add a so-what
        has_hot_cpi = any("cpi" in e["event"].lower() and e["surprise"] == "above" for e in surprises)
        has_strong_retail = any("retail" in e["event"].lower() and e["surprise"] == "above" for e in surprises)
        if has_hot_cpi and has_strong_retail:
            para2 += (
                " The combination of hot inflation and strong consumer spending "
                "paints a picture of an economy that's running warm -- good for "
                "earnings, but it keeps rate cuts off the table for now."
            )
        elif has_hot_cpi:
            para2 += " Sticky inflation remains the story to watch heading into next week."
        elif has_strong_retail:
            para2 += " Consumer strength is encouraging, but watch whether it feeds through to prices."
    else:
        para2 = "It was a quiet week on the data front, with no major surprises."

    # Third paragraph: look-ahead
    upcoming = econ.get("upcoming_week", [])
    high_importance = [e for e in upcoming if e.get("importance", 0) >= 3]
    if high_importance:
        event_names = [e["event"] for e in high_importance]
        para3 = (
            "Looking ahead, the key events to watch are: "
            + ", ".join(event_names)
            + ". Position sizing and hedges should reflect the potential for volatility around these releases."
        )
    else:
        para3 = "Next week's calendar is lighter -- a good time to review positions and rebalance."

    return f"{para1}\n\n{para2}\n\n{para3}"


def generate_positioning_tips(econ, index_data=None):
    """Generate rule-based positioning tips from economic events and index data.

    Rules:
    - CPI above expected -> consider defensives / TIPS
    - Retail sales beat -> lean cyclicals
    - FOMC minutes upcoming -> reduce position size
    - PMI upcoming -> watch industrials
    - Jobless claims below expected -> labor market strong, stay risk-on
    - USD strong -> headwind for multinationals/commodities
    - USD weak -> tailwind for EM and commodities
    """
    tips = []
    past = econ.get("past_week", [])
    upcoming = econ.get("upcoming_week", [])

    # USD-based tips
    if index_data:
        usd = next((i for i in index_data if i["name"] == "USD Index"), None)
        if usd and abs(usd["weekly_pct"]) >= 0.5:
            if usd["weekly_pct"] > 0:
                tips.append(
                    f"USD Index strengthened {usd['weekly_pct']:+.2f}% this week -- "
                    "a stronger dollar weighs on multinational earnings and commodities. "
                    "Consider reducing exposure to export-heavy sectors and commodity ETFs (GLD, DJP)."
                )
            else:
                tips.append(
                    f"USD Index weakened {usd['weekly_pct']:+.2f}% this week -- "
                    "a softer dollar is a tailwind for emerging markets (EEM, VWO) and commodities (GLD, DJP). "
                    "Consider tilting toward international and commodity exposure."
                )

    for event in past:
        name = event.get("event", "").lower()
        surprise = event.get("surprise", "")

        if "cpi" in name and "core" not in name and surprise == "above":
            tips.append(
                "CPI came in hot at {actual}{unit} vs. {expected}{unit} expected -- "
                "inflation-sensitive sectors may see pressure. "
                "Consider TIPS (TIP) or defensive tilts (XLU, XLP).".format(**event)
            )
        if "retail sales" in name and surprise == "above":
            tips.append(
                "Retail sales surprised to the upside ({actual}{unit} vs. {expected}{unit}) -- "
                "consumer discretionary (XLY) and cyclicals may benefit.".format(**event)
            )
        if "jobless claims" in name and surprise == "below":
            tips.append(
                "Jobless claims came in lower than expected ({actual:,} vs. {expected:,}) -- "
                "labor market remains tight, supporting risk-on positioning.".format(**event)
            )
        if "services pmi" in name and surprise == "below":
            tips.append(
                "Services PMI missed at {actual} vs. {expected} expected -- "
                "services sector contraction is a caution signal. "
                "Consider trimming consumer discretionary (XLY) and adding defensives (XLP, XLU).".format(**event)
            )
        if "housing starts" in name and surprise == "below":
            tips.append(
                "Housing Starts missed at {actual}{unit} vs. {expected}{unit} -- "
                "affordability pressure weighs on homebuilders (ITB, XHB). "
                "Watch mortgage rate trajectory before adding real estate exposure.".format(**event)
            )

    for event in upcoming:
        name = event.get("event", "").lower()
        if "fomc" in name:
            tips.append(
                "FOMC Meeting Minutes drop {date} -- expect volatility. "
                "Consider trimming position sizes or hedging with VIX calls.".format(**event)
            )
        if "pmi" in name and "manufacturing" in name:
            tips.append(
                "Flash Manufacturing PMI on {date} -- a key read on factory activity. "
                "Watch industrials (XLI) for directional cues.".format(**event)
            )
        if "pce" in name:
            tips.append(
                "PCE Price Index on {date} -- the Fed's preferred inflation gauge. "
                "A hot print could reprice rate-cut expectations; consider hedging bond duration (TLT) "
                "and adding inflation protection (TIPS, GLD).".format(**event)
            )
        if "gdp" in name:
            tips.append(
                "GDP release on {date} -- a weak print could shift sentiment toward defensives (XLU, XLP); "
                "a strong beat supports risk-on positioning in cyclicals (XLY, XLI).".format(**event)
            )

    if not tips:
        tips.append("No strong macro signals this week -- maintain current allocations.")

    return tips


def build_template_context(index_data, econ, date_str):
    """Assemble the full context dict for the Jinja2 template.

    Args:
        index_data: List from process_index_data.
        econ: Raw econ calendar dict.
        date_str: The newsletter date (YYYY-MM-DD).

    Returns:
        Dict ready for Jinja2 rendering.
    """
    tips = generate_positioning_tips(econ, index_data)
    narrative = generate_narrative(index_data, econ)

    best = index_data[0] if index_data else None
    worst = index_data[-1] if index_data else None

    return {
        "date": date_str,
        "narrative": narrative,
        "indices": index_data,
        "best": best,
        "worst": worst,
        "past_events": econ.get("past_week", []),
        "upcoming_events": econ.get("upcoming_week", []),
        "tips": tips,
    }
