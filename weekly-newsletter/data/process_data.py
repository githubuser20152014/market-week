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

        entry = {
            "name": name,
            "symbol": info["symbol"],
            "close": last_close,
            "weekly_pct": round(weekly_pct, 2),
            "week_high": week_high,
            "week_low": week_low,
        }
        if "treasury" in name.lower():
            entry["yield_change_bps"] = round((last_close - first_open) * 100, 1)
            entry["is_yield"] = True
        results.append(entry)

    results.sort(key=lambda x: x["weekly_pct"], reverse=True)
    return results


def generate_narrative(index_data, econ):
    """Generate a top-of-newsletter narrative summarizing the week.

    Reads the index performance and economic events to produce a
    2-3 paragraph plain-English summary an investor can scan quickly.
    """
    if not index_data:
        return "Markets were closed this week."

    # Find gold, treasury, and USD specifically
    gold = next((i for i in index_data if i["name"] == "Gold"), None)
    treasury = next((i for i in index_data if "Treasury" in i["name"]), None)
    usd = next((i for i in index_data if i["name"] == "USD Index"), None)

    # Equity indices only — exclude gold, treasury, USD from best/worst ranking
    # (treasury weekly_pct is yield % change, not price return; comparing it to
    # equity % returns is misleading)
    _NON_EQUITY = {"Gold", "USD Index"}
    equity_indices = [
        i for i in index_data
        if i["name"] not in _NON_EQUITY and "Treasury" not in i["name"]
    ]
    ranked = equity_indices if equity_indices else index_data
    best = ranked[0]
    worst = ranked[-1]

    # Count direction across equity indices only
    up_count = sum(1 for i in equity_indices if i["weekly_pct"] > 0)
    down_count = len(equity_indices) - up_count

    # Build the opening paragraph about overall market direction
    if not equity_indices:
        tone = "Markets were mixed this week"
    elif up_count == len(equity_indices):
        tone = "Markets rallied across the board this week"
    elif down_count == len(equity_indices):
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


def generate_plain_english_summary(index_data, econ):
    """Generate a plain-English 'What This Means' section for active investors.

    Written for someone who just read the data and wants the so-what —
    no jargon, no abbreviations unexplained, just clear takeaways.
    """
    if not index_data:
        return "Not enough data to summarize this week."

    lines = []

    # ── 1. What happened in markets ──────────────────────────────────────────
    sp = next((i for i in index_data if "S&P" in i["name"]), None)
    nasdaq = next((i for i in index_data if "Nasdaq" in i["name"]), None)
    dow = next((i for i in index_data if "Dow" in i["name"]), None)
    gold = next((i for i in index_data if i["name"] == "Gold"), None)
    treasury = next((i for i in index_data if "Treasury" in i["name"]), None)
    usd = next((i for i in index_data if i["name"] == "USD Index"), None)

    up_indices = [i for i in index_data if i["weekly_pct"] > 0 and i["name"] not in ("Gold", "USD Index", "10Y Treasury")]
    down_indices = [i for i in index_data if i["weekly_pct"] < 0 and i["name"] not in ("Gold", "USD Index", "10Y Treasury")]

    # Stock market direction sentence
    if sp:
        if sp["weekly_pct"] > 1.5:
            stock_line = (f"**Stocks had a strong week.** The S&P 500 gained {sp['weekly_pct']:+.1f}%, "
                          f"meaning a $10,000 portfolio tracking it grew by about ${abs(sp['weekly_pct']) * 100:,.0f}.")
        elif sp["weekly_pct"] > 0:
            stock_line = (f"**Stocks inched higher but nothing to write home about.** The S&P 500 was up just "
                          f"{sp['weekly_pct']:+.1f}% — markets moved but didn't go anywhere decisive.")
        elif sp["weekly_pct"] > -1.5:
            stock_line = (f"**Stocks slipped modestly.** The S&P 500 lost {sp['weekly_pct']:.1f}% — a quiet "
                          f"pullback, not a panic, but the direction was down.")
        else:
            stock_line = (f"**Stocks had a rough week.** The S&P 500 dropped {sp['weekly_pct']:.1f}%, "
                          f"meaning a $10,000 portfolio tracking it lost about ${abs(sp['weekly_pct']) * 100:,.0f}.")
        lines.append(stock_line)

    # Tech vs broader market split
    if nasdaq and sp:
        diff = nasdaq["weekly_pct"] - sp["weekly_pct"]
        if diff > 0.8:
            lines.append(f"Tech led the way — Nasdaq outperformed the broader market by {diff:.1f} percentage points, "
                         f"meaning growth and tech stocks had a relatively better week.")
        elif diff < -0.8:
            lines.append(f"Tech lagged — Nasdaq underperformed the broader market by {abs(diff):.1f} percentage points. "
                         f"If you're heavy in tech ETFs, this week stung a bit more.")

    # Gold signal
    if gold:
        if gold["weekly_pct"] > 1.5:
            lines.append(f"**Gold surged {gold['weekly_pct']:+.1f}% to ${gold['close']:,.0f}.** "
                         f"When gold runs like this it usually means investors are nervous — they're moving money "
                         f"to something that holds value when everything else feels uncertain.")
        elif gold["weekly_pct"] < -1.5:
            lines.append(f"**Gold fell {gold['weekly_pct']:.1f}%.** Investors feel confident enough that they're not "
                         f"rushing to safety. That's generally a good sign for risk assets.")
        elif gold["weekly_pct"] > 0:
            lines.append(f"Gold was up slightly ({gold['weekly_pct']:+.1f}%) — a mild safe-haven bid, "
                         f"but nothing that signals serious alarm.")

    # Treasury yield signal
    if treasury:
        if treasury["weekly_pct"] < -2:
            lines.append(f"**Bond yields fell sharply** (the 10-year Treasury dropped to {treasury['close']:.2f}%). "
                         f"Lower yields mean the bond market thinks the economy may be slowing, "
                         f"or that inflation is cooling — either way, it's a signal worth watching. "
                         f"It also means existing bonds in your portfolio went up in value.")
        elif treasury["weekly_pct"] > 2:
            lines.append(f"**Bond yields rose** (the 10-year Treasury climbed to {treasury['close']:.2f}%). "
                         f"Rising yields mean bonds are losing value — if you hold long-dated bond ETFs (like TLT), "
                         f"that hurt this week. It also makes borrowing more expensive, which weighs on growth stocks.")
        else:
            lines.append(f"Bond yields were relatively stable at {treasury['close']:.2f}% — "
                         f"no dramatic signal from the rates market this week.")

    # USD signal
    if usd and abs(usd["weekly_pct"]) >= 0.4:
        if usd["weekly_pct"] > 0:
            lines.append(f"The dollar strengthened {usd['weekly_pct']:+.1f}%. A stronger dollar is a quiet headwind "
                         f"if you hold international stock ETFs — the gains overseas get partially erased when "
                         f"converted back to USD.")
        else:
            lines.append(f"The dollar weakened {usd['weekly_pct']:.1f}%. A softer dollar is a tailwind for "
                         f"international ETFs and commodities like gold — it makes foreign assets worth more in "
                         f"dollar terms when you bring the money home.")

    # ── 2. What the economic data meant in plain English ─────────────────────
    past = econ.get("past_week", [])
    data_lines = []

    for ev in past:
        name = ev.get("event", "")
        surprise = ev.get("surprise", "neutral")
        actual = ev.get("actual", "--")
        unit = ev.get("unit", "")

        name_lower = name.lower()

        if "consumer confidence" in name_lower:
            if surprise == "above":
                data_lines.append(f"The Consumer Confidence index came in at {actual} — higher than expected. "
                                   f"Translation: everyday Americans feel relatively okay about their jobs and finances. "
                                   f"That tends to support continued spending, which is good for the economy.")
            elif surprise == "below":
                data_lines.append(f"Consumer Confidence disappointed at {actual}. "
                                   f"People are feeling less optimistic about the economy — when confidence drops, "
                                   f"spending usually follows. Worth monitoring.")

        elif "ppi" in name_lower or "producer price" in name_lower:
            if surprise == "above":
                data_lines.append(f"The Producer Price Index — basically what businesses pay for their inputs — "
                                   f"came in hotter than expected at {actual}{unit}. "
                                   f"This matters because when businesses pay more to make things, "
                                   f"they eventually pass those costs on to you as higher prices. "
                                   f"It also signals the Fed probably won't be cutting interest rates anytime soon.")
            elif surprise == "below":
                data_lines.append(f"Producer prices came in cooler than expected — good news on the inflation front. "
                                   f"Lower input costs for businesses can eventually mean lower prices for consumers, "
                                   f"and it gives the Fed more room to think about cutting rates.")

        elif "pce" in name_lower:
            if surprise == "above":
                data_lines.append(f"The PCE inflation reading — the Fed's preferred way to measure inflation — "
                                   f"came in hotter than expected at {actual}{unit}. "
                                   f"This is a big deal: it tells the Fed that inflation isn't beaten yet, "
                                   f"making interest rate cuts less likely and keeping pressure on stocks.")
            elif surprise == "below":
                data_lines.append(f"PCE inflation — the Fed's preferred gauge — cooled more than expected. "
                                   f"That's the kind of data the Fed needs to see before cutting rates. "
                                   f"Good news for growth stocks and bond prices.")

        elif "cpi" in name_lower:
            if surprise == "above":
                data_lines.append(f"Inflation (CPI) ran hotter than expected at {actual}{unit}. "
                                   f"Higher-than-expected inflation means the Fed is less likely to cut interest rates soon. "
                                   f"Rate cuts are generally good for stocks — so this delays that tailwind.")
            elif surprise == "below":
                data_lines.append(f"Inflation (CPI) came in cooler than expected at {actual}{unit}. "
                                   f"Progress on inflation gives the Fed more room to cut interest rates, "
                                   f"which tends to be a positive for both stocks and bonds.")

        elif "gdp" in name_lower:
            if surprise == "above":
                data_lines.append(f"GDP — the broadest measure of economic output — beat expectations at {actual}{unit}. "
                                   f"A stronger economy generally means better corporate earnings ahead.")
            elif surprise == "below":
                data_lines.append(f"GDP growth came in below expectations at {actual}{unit}. "
                                   f"The economy grew, but more slowly than hoped — a reminder that growth isn't guaranteed. "
                                   f"Defensives (utilities, consumer staples) tend to hold up better in slower-growth environments.")

        elif "tariff" in name_lower or "scotus" in name_lower:
            data_lines.append(f"The big non-data story this week was trade policy. A court ruling challenged existing tariffs, "
                               f"and a new 10% blanket import tax was announced. "
                               f"Tariffs raise costs for U.S. companies that import goods — that pressure can squeeze profit margins "
                               f"and eventually show up as higher prices. It's adding an extra layer of uncertainty "
                               f"that the market doesn't love.")

        elif "durable goods" in name_lower:
            if surprise == "above":
                data_lines.append(f"Durable goods orders — think big purchases like machinery and equipment — "
                                   f"beat expectations. Businesses are still investing, which is a healthy economic signal.")
            elif surprise == "below":
                data_lines.append(f"Durable goods orders disappointed. Businesses are pulling back on big-ticket purchases "
                                   f"— a caution signal for the industrial and manufacturing sector.")

        elif "services pmi" in name_lower or "flash services" in name_lower:
            if surprise == "below" and actual != "--":
                try:
                    val = float(actual)
                    if val < 50:
                        data_lines.append(f"The services sector — which drives most of the U.S. economy — "
                                           f"unexpectedly contracted (PMI of {actual}, below the 50 line that separates "
                                           f"growth from contraction). That's a meaningful warning sign.")
                    else:
                        data_lines.append(f"Services activity expanded but came in softer than expected at {actual}. "
                                           f"The services sector is still growing but losing momentum.")
                except (ValueError, TypeError):
                    pass

        elif "manufacturing pmi" in name_lower or "flash manufacturing" in name_lower:
            if actual != "--":
                try:
                    val = float(actual)
                    if val > 50:
                        data_lines.append(f"Manufacturing activity expanded this week (PMI of {actual}). "
                                           f"Factories are busier — generally positive for industrial stocks.")
                    else:
                        data_lines.append(f"Manufacturing activity contracted (PMI of {actual}, below 50). "
                                           f"A slowdown in factory output can signal broader economic weakness ahead.")
                except (ValueError, TypeError):
                    pass

    if data_lines:
        lines.append("\n**On the economic data front:**")
        lines.extend([f"- {dl}" for dl in data_lines])

    # ── 3. Bottom line ────────────────────────────────────────────────────────
    upcoming = econ.get("upcoming_week", [])
    high_next = [e for e in upcoming if e.get("importance", 0) >= 3]

    # Assess overall macro tone
    hot_inflation = any(
        ("ppi" in e.get("event", "").lower() or "pce" in e.get("event", "").lower() or "cpi" in e.get("event", "").lower())
        and e.get("surprise") == "above"
        for e in past
    )
    tariff_risk = any("tariff" in e.get("event", "").lower() or "scotus" in e.get("event", "").lower() for e in past)

    bottom = []
    if hot_inflation and tariff_risk:
        bottom.append("**The bottom line:** It was an uncomfortable week to be an investor. "
                       "Inflation is still sticky, trade policy is unpredictable, and the Fed has no reason to rescue "
                       "markets with rate cuts yet. That's not a reason to panic — but it is a reason to make sure "
                       "your portfolio isn't leaning too hard into rate-sensitive or import-dependent sectors.")
    elif hot_inflation:
        bottom.append("**The bottom line:** Inflation data came in hotter than hoped. "
                       "Until that cools, don't expect the Fed to ride to the rescue with rate cuts. "
                       "Portfolios tilted toward growth and long-duration bonds may face continued headwinds.")
    elif tariff_risk:
        bottom.append("**The bottom line:** Trade policy uncertainty is the dominant theme right now. "
                       "Markets don't like uncertainty, and tariffs add costs across many sectors. "
                       "Domestically-focused companies tend to be less exposed than global multinationals.")
    elif gold and gold["weekly_pct"] > 1.5 and sp and sp["weekly_pct"] < 0:
        bottom.append("**The bottom line:** Investors were in risk-off mode this week — "
                       "selling stocks and buying gold. It's a defensive posture. "
                       "Not necessarily a signal to sell everything, but worth checking whether your portfolio "
                       "has enough defensive exposure for this kind of environment.")
    elif sp and sp["weekly_pct"] > 1:
        bottom.append("**The bottom line:** A solid week. The macro backdrop is supportive, "
                       "and the market reflected that. Stay invested but keep an eye on the data "
                       "coming next week — a surprise in either direction can quickly change the tone.")
    else:
        bottom.append("**The bottom line:** A relatively uneventful week with no dramatic shifts. "
                       "Use quiet weeks like this to review your allocations rather than react to noise.")

    if high_next:
        next_names = [e["event"] for e in high_next[:2]]
        bottom.append(f"**Watch next week:** {' and '.join(next_names)} are the key releases. "
                       f"These can move markets — particularly bonds and rate-sensitive sectors — "
                       f"so it's worth being positioned before the prints rather than reacting after.")

    lines.extend(bottom)

    return "\n\n".join(lines)


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
                    f"USD Index strengthened {usd['weekly_pct']:+.2f}% this week"
                    " -- a stronger dollar weighs on multinational earnings and commodities. "
                    "Consider reducing exposure to export-heavy sectors and commodity ETFs (GLD, DJP)."
                )
            else:
                tips.append(
                    f"USD Index weakened {usd['weekly_pct']:+.2f}% this week"
                    " -- a softer dollar is a tailwind for emerging markets (EEM, VWO) and commodities (GLD, DJP). "
                    "Consider tilting toward international and commodity exposure."
                )

    for event in past:
        name = event.get("event", "").lower()
        surprise = event.get("surprise", "")

        if "cpi" in name and "core" not in name and surprise == "above":
            tips.append(
                "CPI came in hot at {actual}{unit} vs. {expected}{unit} expected"
                " -- inflation-sensitive sectors may see pressure. "
                "Consider TIPS (TIP) or defensive tilts (XLU, XLP).".format(**event)
            )
        if "retail sales" in name and surprise == "above":
            tips.append(
                "Retail sales surprised to the upside ({actual}{unit} vs. {expected}{unit})"
                " -- consumer discretionary (XLY) and cyclicals may benefit.".format(**event)
            )
        if "jobless claims" in name and surprise == "below":
            tips.append(
                "Jobless claims came in lower than expected ({actual:,} vs. {expected:,})"
                " -- labor market remains tight, supporting risk-on positioning.".format(**event)
            )
        if "services pmi" in name and surprise == "below":
            tips.append(
                "Services PMI missed at {actual} vs. {expected} expected"
                " -- services sector contraction is a caution signal. "
                "Consider trimming consumer discretionary (XLY) and adding defensives (XLP, XLU).".format(**event)
            )
        if "housing starts" in name and surprise == "below":
            tips.append(
                "Housing Starts missed at {actual}{unit} vs. {expected}{unit}"
                " -- affordability pressure weighs on homebuilders (ITB, XHB). "
                "Watch mortgage rate trajectory before adding real estate exposure.".format(**event)
            )

    for event in upcoming:
        name = event.get("event", "").lower()
        if "fomc" in name:
            tips.append(
                "FOMC Meeting Minutes on {date}"
                " -- expect volatility. Consider trimming position sizes or hedging with VIX calls.".format(**event)
            )
        if "pmi" in name and "manufacturing" in name:
            tips.append(
                "Flash Manufacturing PMI on {date}"
                " -- a key read on factory activity. Watch industrials (XLI) for directional cues.".format(**event)
            )
        if "pce" in name:
            tips.append(
                "PCE Price Index on {date}"
                " -- the Fed's preferred inflation gauge. "
                "A hot print could reprice rate-cut expectations; consider hedging bond duration (TLT) "
                "and adding inflation protection (TIPS, GLD).".format(**event)
            )
        if "gdp" in name:
            tips.append(
                "GDP release on {date}"
                " -- a weak print could shift sentiment toward defensives (XLU, XLP); "
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
    plain_summary = generate_plain_english_summary(index_data, econ)

    best = index_data[0] if index_data else None
    worst = index_data[-1] if index_data else None

    return {
        "date": date_str,
        "narrative": narrative,
        "plain_summary": plain_summary,
        "indices": index_data,
        "best": best,
        "worst": worst,
        "past_events": econ.get("past_week", []),
        "upcoming_events": econ.get("upcoming_week", []),
        "tips": tips,
    }
