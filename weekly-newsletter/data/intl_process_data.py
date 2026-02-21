"""Process international index and FX data into newsletter-ready content."""

# Human-readable names for FX pairs (used in narrative and tips)
FX_FRIENDLY = {
    "EUR/USD": "the Euro",
    "GBP/USD": "the British Pound",
    "JPY/USD": "the Japanese Yen",
    "AUD/USD": "the Australian Dollar",
    "CHF/USD": "the Swiss Franc",
}


def process_intl_index_data(raw):
    """Compute weekly performance for each international index.

    Args:
        raw: Dict from fetch_intl_index_data, keyed by index name.

    Returns:
        List of dicts sorted by weekly_pct (best to worst), each with:
        name, symbol, region, close, weekly_pct, week_high, week_low
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
            "region": info.get("region", ""),
            "close": last_close,
            "weekly_pct": round(weekly_pct, 2),
            "week_high": week_high,
            "week_low": week_low,
        })

    results.sort(key=lambda x: x["weekly_pct"], reverse=True)
    return results


def process_fx_data(raw):
    """Compute weekly % change for each FX pair.

    Args:
        raw: Dict from fetch_intl_fx_data, keyed by pair name.

    Returns:
        List of dicts with: name, symbol, rate, weekly_pct
    """
    results = []
    for name, info in raw.items():
        data = info["data"]
        if len(data) < 2:
            continue
        first_open = data[0]["open"]
        last_close = data[-1]["close"]
        weekly_pct = ((last_close - first_open) / first_open) * 100

        results.append({
            "name": name,
            "symbol": info["symbol"],
            "rate": round(last_close, 6),
            "weekly_pct": round(weekly_pct, 2),
        })

    results.sort(key=lambda x: x["weekly_pct"], reverse=True)
    return results


def _join_list(items):
    """Join a list of strings with commas and 'and' before the last item."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def generate_intl_narrative(index_data, fx_data, econ):
    """Generate a top-of-newsletter narrative summarising the global week.

    Three paragraphs:
    1. Overall direction, best/worst performers, regional spread.
    2. Central bank and economic drivers, FX context.
    3. Look-ahead to high-importance upcoming events.
    """
    if not index_data:
        return "International markets were closed this week."

    best = index_data[0]
    worst = index_data[-1]

    up_count = sum(1 for i in index_data if i["weekly_pct"] > 0)
    down_count = len(index_data) - up_count

    if up_count == len(index_data):
        tone = "Global markets rallied broadly this week"
    elif down_count == len(index_data):
        tone = "It was a difficult week across international markets"
    elif up_count > down_count:
        tone = "International markets posted mostly gains this week"
    else:
        tone = "International markets were mixed this week"

    para1 = (
        f"{tone}, with {best['name']} ({best['region']}) leading at {best['weekly_pct']:+.2f}% "
        f"and {worst['name']} ({worst['region']}) lagging at {worst['weekly_pct']:+.2f}%."
    )

    # Add regional colour
    europe = [i for i in index_data if i.get("region") == "Europe"]
    apac = [i for i in index_data if i.get("region") == "Asia-Pacific"]
    em = [i for i in index_data if i.get("region") == "Emerging Markets"]

    region_notes = []
    if europe:
        avg_eu = sum(i["weekly_pct"] for i in europe) / len(europe)
        direction = "outperformed" if avg_eu > 0 else "underperformed"
        region_notes.append(f"European indices {direction} on average ({avg_eu:+.2f}%)")
    if apac:
        avg_ap = sum(i["weekly_pct"] for i in apac) / len(apac)
        direction = "led" if avg_ap > 0 else "lagged"
        region_notes.append(f"Asia-Pacific {direction} ({avg_ap:+.2f}% average)")
    if em:
        em_pct = em[0]["weekly_pct"]
        region_notes.append(f"Emerging Markets (MSCI EM) moved {em_pct:+.2f}%")

    if region_notes:
        para1 += " " + "; ".join(region_notes) + "."

    # FX context: build a clean comma-separated sentence, "against the USD" once at the end
    fx_notes = []
    for fx in fx_data:
        if abs(fx["weekly_pct"]) >= 0.3:
            direction = "strengthened" if fx["weekly_pct"] > 0 else "weakened"
            friendly = FX_FRIENDLY.get(fx["name"], fx["name"])
            fx_notes.append(f"{friendly} {direction} {abs(fx['weekly_pct']):.2f}%")
    if fx_notes:
        para1 += " On the FX front, " + _join_list(fx_notes) + ", all against the USD."

    # Para 2: Economic drivers
    past = econ.get("past_week", [])
    surprises = [e for e in past if e.get("surprise") in ("above", "below")]

    if surprises:
        drivers = []
        for e in surprises:
            name = e["event"]
            unit = e.get("unit", "")
            if e["surprise"] == "above":
                drivers.append(
                    f"{name} came in above expectations ({e['actual']}{unit} vs. {e['expected']}{unit})"
                )
            else:
                drivers.append(
                    f"{name} came in below expectations ({e['actual']}{unit} vs. {e['expected']}{unit})"
                )

        para2 = "The macro picture was eventful. " + ". ".join(drivers) + "."

        has_hot_cpi = any(
            "cpi" in e["event"].lower() and e["surprise"] == "above" for e in surprises
        )
        has_weak_gdp = any(
            "gdp" in e["event"].lower() and e["surprise"] == "below" for e in surprises
        )
        if has_hot_cpi and has_weak_gdp:
            para2 += (
                " The combination of sticky inflation and weak growth (a stagflationary signal)"
                " puts central banks in a difficult position and argues for a cautious stance"
                " on duration and rate-sensitive sectors."
            )
        elif has_hot_cpi:
            para2 += (
                " Sticky inflation complicates the rate-cut timeline for the relevant central bank."
                " Monitor upcoming policy meetings closely."
            )
        elif has_weak_gdp:
            para2 += (
                " Growth weakness raises the probability of earlier rate cuts,"
                " which could be supportive for bond proxies and interest-rate-sensitive sectors."
            )
    else:
        para2 = "It was a quiet week on the international data front, with no major surprises."

    # Para 3: Look-ahead
    upcoming = econ.get("upcoming_week", [])
    high_importance = [e for e in upcoming if e.get("importance", 0) >= 3]
    if high_importance:
        event_names = [e["event"] for e in high_importance]
        para3 = (
            "Looking ahead, key events to watch are: "
            + ", ".join(event_names)
            + ". Central bank decisions in particular can drive sharp FX and equity moves;"
            " position sizing should reflect that risk."
        )
    else:
        para3 = (
            "Next week's international calendar is lighter, making it a good time to review"
            " regional allocations and currency hedging ratios."
        )

    return f"{para1}\n\n{para2}\n\n{para3}"


def generate_intl_positioning_tips(econ, index_data=None, fx_data=None):
    """Generate rule-based positioning tips from international economic events and data.

    Rules cover:
    - Central bank decisions (ECB, BOJ, BOE)
    - FX moves and their impact on unhedged international ETFs
    - Regional economic surprises (UK CPI, Japan GDP, China PMI)
    - Upcoming high-importance events (risk-sizing signals)
    """
    tips = []
    past = econ.get("past_week", [])
    upcoming = econ.get("upcoming_week", [])

    # FX-driven tips
    if fx_data:
        eur = next((fx for fx in fx_data if fx["name"] == "EUR/USD"), None)
        gbp = next((fx for fx in fx_data if fx["name"] == "GBP/USD"), None)
        jpy = next((fx for fx in fx_data if fx["name"] == "JPY/USD"), None)
        aud = next((fx for fx in fx_data if fx["name"] == "AUD/USD"), None)

        if eur and abs(eur["weekly_pct"]) >= 0.3:
            if eur["weekly_pct"] < 0:
                tips.append(
                    f"The Euro weakened {abs(eur['weekly_pct']):.2f}% against the USD: a headwind for unhedged European"
                    " equity exposure (EFA, FEZ, EWG). Consider currency-hedged alternatives (HEDJ)"
                    " or reduce European allocation until the Euro stabilises."
                )
            else:
                tips.append(
                    f"The Euro strengthened {abs(eur['weekly_pct']):.2f}% against the USD: a tailwind for unhedged"
                    " European equity ETFs (EFA, FEZ, EWG). Currency momentum favours holding"
                    " unhedged exposure for now."
                )

        if jpy and abs(jpy["weekly_pct"]) >= 0.3:
            if jpy["weekly_pct"] < 0:
                tips.append(
                    f"The Japanese Yen weakened {abs(jpy['weekly_pct']):.2f}% against the USD:"
                    " this reduces USD returns on unhedged Japan exposure (EWJ). Watch BOJ policy signals;"
                    " any rate hike could trigger a sharp Yen reversal."
                )
            else:
                tips.append(
                    f"The Japanese Yen strengthened {abs(jpy['weekly_pct']):.2f}% against the USD:"
                    " this boosts USD returns on unhedged Japan ETFs (EWJ). Yen strengthening often signals"
                    " risk-off sentiment; monitor carry-trade unwind risk for EM assets."
                )

        if aud and abs(aud["weekly_pct"]) >= 0.3:
            if aud["weekly_pct"] < 0:
                tips.append(
                    f"The Australian Dollar weakened {abs(aud['weekly_pct']):.2f}% against the USD: a headwind for unhedged"
                    " Australian equity exposure (EWA). AUD weakness often tracks commodity"
                    " prices and China growth sentiment."
                )

    # Event-driven tips
    for event in past:
        name = event.get("event", "").lower()
        surprise = event.get("surprise", "")

        if "uk cpi" in name and surprise == "above":
            tips.append(
                "UK CPI came in above expectations ({actual}{unit} vs. {expected}{unit}):"
                " a higher-for-longer BOE rate path is now more likely. GBP may stay supported"
                " (positive for FXB), but rate pressure is a headwind for UK rate-sensitive sectors."
                " Watch EWU for near-term volatility around the next BOE meeting.".format(**event)
            )

        if ("japan" in name or "japan gdp" in name) and "gdp" in name and surprise == "below":
            tips.append(
                "Japan GDP contracted below expectations ({actual}{unit} vs. {expected}{unit}):"
                " growth weakness reduces the BOJ's appetite for further rate hikes."
                " Consider reducing EWJ near-term; a dovish BOJ would weaken the Yen and compress"
                " USD returns on Japan equities.".format(**event)
            )

        if ("china" in name or "caixin" in name) and "pmi" in name:
            if surprise == "above":
                tips.append(
                    "China Caixin PMI beat at {actual} vs. {expected} expected:"
                    " domestic demand momentum supports EM risk-on positioning."
                    " Consider adding exposure via EEM or FXI on dips.".format(**event)
                )
            elif surprise == "below":
                tips.append(
                    "China PMI missed at {actual} vs. {expected} expected:"
                    " growth concerns warrant caution on China-heavy EM exposure (FXI, EEM)."
                    " Commodity exporters (EWA, EWC) may also face headwinds.".format(**event)
                )

        if "ecb" in name and "minute" in name:
            tips.append(
                "ECB Meeting Minutes were released: review the tone for signals on the rate path."
                " A hawkish-leaning ECB supports EUR and could weigh on European bond proxies;"
                " a dovish lean favours EFA and FEZ through rate-cut expectations."
            )

    # Upcoming event tips
    for event in upcoming:
        name = event.get("event", "").lower()

        if "ecb rate" in name or "ecb policy" in name:
            tips.append(
                "ECB Rate Decision on {date}: a key event for EUR and European equities."
                " Reduce position size in EFA, FEZ, EWG ahead of the announcement;"
                " a surprise cut or hawkish hold could drive outsized FX and equity moves.".format(
                    **event
                )
            )

        if "boj" in name:
            tips.append(
                "BOJ Meeting Minutes on {date}: watch for any YCC or rate-hike signals."
                " A hawkish surprise would likely strengthen the Yen sharply and create volatility in"
                " unhedged Japan exposure (EWJ). Carry-trade unwinding could ripple into EM assets.".format(
                    **event
                )
            )

        if "eurozone cpi" in name or "euro cpi" in name:
            tips.append(
                "Eurozone CPI Flash on {date}: a hot print would extend the ECB hold and pressure"
                " European bond proxies, while a soft print opens the door for H2 rate cuts,"
                " supportive of EFA, FEZ, and EUR-denominated duration.".format(**event)
            )

        if "boe" in name or ("uk" in name and "rate" in name):
            tips.append(
                "BOE Rate Decision on {date}: a hawkish hold or hike would support GBP (FXB)"
                " but weigh on UK rate-sensitive sectors. Watch EWU for directional cues.".format(
                    **event
                )
            )

    if not tips:
        tips.append(
            "No strong macro signals from international markets this week:"
            " maintain current regional allocations."
        )

    return tips


def build_intl_template_context(index_data, fx_data, econ, date_str):
    """Assemble the full context dict for the international Jinja2 template.

    Args:
        index_data: List from process_intl_index_data.
        fx_data: List from process_fx_data.
        econ: Raw international econ calendar dict.
        date_str: The newsletter date (YYYY-MM-DD).

    Returns:
        Dict ready for Jinja2 rendering.
    """
    tips = generate_intl_positioning_tips(econ, index_data, fx_data)
    narrative = generate_intl_narrative(index_data, fx_data, econ)

    best = index_data[0] if index_data else None
    worst = index_data[-1] if index_data else None

    return {
        "date": date_str,
        "narrative": narrative,
        "indices": index_data,
        "best": best,
        "worst": worst,
        "fx_rates": fx_data,
        "past_events": econ.get("past_week", []),
        "upcoming_events": econ.get("upcoming_week", []),
        "tips": tips,
    }
