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


def generate_narrative(index_data, econ, news_items=None):
    """Generate a top-of-newsletter narrative summarizing the week.

    Produces 4–5 paragraphs covering: equity breadth, rates/gold/dollar,
    dominant themes, economic data, and a look-ahead.
    """
    if not index_data:
        return "Markets were closed this week."

    if news_items is None:
        news_items = []

    _NON_EQUITY = {"Gold", "USD Index", "WTI Crude Oil"}
    gold     = next((i for i in index_data if i["name"] == "Gold"), None)
    treasury = next((i for i in index_data if "Treasury" in i["name"]), None)
    usd      = next((i for i in index_data if i["name"] == "USD Index"), None)
    oil      = next((i for i in index_data if "Crude" in i["name"] or "WTI" in i["name"]), None)
    sp       = next((i for i in index_data if "S&P" in i["name"]), None)
    nasdaq   = next((i for i in index_data if "Nasdaq" in i["name"]), None)
    dow      = next((i for i in index_data if "Dow" in i["name"]), None)
    russell  = next((i for i in index_data if "Russell" in i["name"]), None)

    equity_indices = [
        i for i in index_data
        if i["name"] not in _NON_EQUITY and "Treasury" not in i["name"]
    ]
    ranked    = equity_indices if equity_indices else index_data
    best      = ranked[0]
    worst     = ranked[-1]
    up_count  = sum(1 for i in equity_indices if i["weekly_pct"] > 0)
    down_count = len(equity_indices) - up_count

    paras = []

    # ── Para 1: Equity breadth — all major indices ────────────────────────────
    if not equity_indices:
        tone = "Markets were mixed this week"
    elif up_count == len(equity_indices):
        tone = "Stocks rallied broadly this week"
    elif down_count == len(equity_indices):
        tone = "It was a down week across the board for equities"
    elif up_count > down_count:
        tone = "Stocks posted mostly gains this week"
    else:
        tone = "Stocks were mixed this week"

    # Build per-index detail for all four major equity indices
    index_details = []
    for idx in [sp, nasdaq, dow, russell]:
        if idx:
            index_details.append(
                f"{idx['name']} closing at {idx['close']:,.2f} ({idx['weekly_pct']:+.2f}%)"
            )

    if index_details:
        para1 = f"{tone}: " + ", ".join(index_details) + "."
    else:
        para1 = (
            f"{tone}, with {best['name']} closing at {best['close']:,.2f} "
            f"({best['weekly_pct']:+.2f}%) and {worst['name']} closing at "
            f"{worst['close']:,.2f} ({worst['weekly_pct']:+.2f}%)."
        )

    # Characterise breadth
    if down_count == len(equity_indices) and len(equity_indices) >= 3:
        para1 += (
            " The decline was broad-based — all major indices moved lower together,"
            " a sign of broad risk-off sentiment rather than isolated sector weakness."
        )
    elif up_count == len(equity_indices) and len(equity_indices) >= 3:
        para1 += (
            " The advance was broad-based — all major indices moved higher together,"
            " a clean risk-on signal."
        )
    elif nasdaq and sp and abs(nasdaq["weekly_pct"] - sp["weekly_pct"]) > 1.0:
        diff = nasdaq["weekly_pct"] - sp["weekly_pct"]
        if diff > 0:
            para1 += (
                f" Tech was the standout, with the Nasdaq outperforming the S&P 500"
                f" by {abs(diff):.1f} percentage points."
            )
        else:
            para1 += (
                f" Tech lagged the broader market, with the Nasdaq underperforming"
                f" the S&P 500 by {abs(diff):.1f} percentage points."
            )

    paras.append(para1)

    # ── Para 2: Rates, gold, dollar ───────────────────────────────────────────
    macro_notes = []

    if treasury:
        tsy_bps = treasury.get("yield_change_bps", 0) or 0
        bps_str = f"{abs(round(tsy_bps))} bps"
        if tsy_bps > 5:
            macro_notes.append(
                f"The 10-year Treasury yield climbed {bps_str} to {treasury['close']:.2f}%"
                f" — rising yields signal the bond market is pricing out rate cuts,"
                f" which puts pressure on rate-sensitive growth stocks and long-duration bonds."
            )
        elif tsy_bps < -5:
            macro_notes.append(
                f"The 10-year Treasury yield dropped {bps_str} to {treasury['close']:.2f}%"
                f" — falling yields typically reflect growth concerns or cooling inflation expectations,"
                f" and lift bond prices."
            )
        else:
            macro_notes.append(
                f"The 10-year Treasury yield ended the week little changed at {treasury['close']:.2f}%,"
                f" providing no strong directional signal from the rates market."
            )

    if gold:
        if gold["weekly_pct"] > 1.5:
            macro_notes.append(
                f"Gold surged {gold['weekly_pct']:+.2f}% to ${gold['close']:,.2f},"
                f" a strong safe-haven bid suggesting investors are seeking cover from uncertainty."
            )
        elif gold["weekly_pct"] < -1.5:
            macro_notes.append(
                f"Gold fell {abs(gold['weekly_pct']):.2f}% to ${gold['close']:,.2f}."
                f" The drop — unusual during an equity selloff — points to dollar strength"
                f" as the dominant force rather than a flight to safety."
            )
        else:
            macro_notes.append(
                f"Gold moved {gold['weekly_pct']:+.2f}% to ${gold['close']:,.2f},"
                f" a modest {'bid' if gold['weekly_pct'] > 0 else 'pullback'} with no strong directional signal."
            )

    if usd:
        if usd["weekly_pct"] > 0.5:
            macro_notes.append(
                f"The dollar strengthened {usd['weekly_pct']:+.2f}% (DXY: {usd['close']:.2f}),"
                f" a headwind for multinational earnings and international ETF holders."
            )
        elif usd["weekly_pct"] < -0.5:
            macro_notes.append(
                f"The dollar weakened {abs(usd['weekly_pct']):.2f}% (DXY: {usd['close']:.2f}),"
                f" a tailwind for international equities and commodities priced in USD."
            )
        else:
            macro_notes.append(
                f"The dollar was largely flat on the week (DXY: {usd['close']:.2f}),"
                f" providing no meaningful currency tailwind or headwind."
            )

    if oil:
        if oil["weekly_pct"] > 5:
            macro_notes.append(
                f"WTI crude surged {oil['weekly_pct']:+.2f}% on the week to ${oil['close']:,.2f}/bbl"
                f" — a sharp move that raises input costs across transportation, manufacturing,"
                f" and consumer goods, and adds an inflationary undercurrent to the macro picture."
            )
        elif oil["weekly_pct"] > 2:
            macro_notes.append(
                f"WTI crude rose {oil['weekly_pct']:+.2f}% to ${oil['close']:,.2f}/bbl"
                f" — a meaningful move that adds upward pressure on energy costs and inflation expectations."
            )
        elif oil["weekly_pct"] < -5:
            macro_notes.append(
                f"WTI crude fell sharply, down {abs(oil['weekly_pct']):.2f}% to ${oil['close']:,.2f}/bbl"
                f" — a significant relief for inflation and consumer spending power."
            )
        elif oil["weekly_pct"] < -2:
            macro_notes.append(
                f"WTI crude slipped {abs(oil['weekly_pct']):.2f}% to ${oil['close']:,.2f}/bbl"
                f" — a modest tailwind for inflation and transport-heavy sectors."
            )
        else:
            macro_notes.append(
                f"WTI crude was little changed on the week at ${oil['close']:,.2f}/bbl"
                f" ({oil['weekly_pct']:+.2f}%)."
            )

    if macro_notes:
        paras.append(" ".join(macro_notes))

    # ── Para 3: Dominant themes ────────────────────────────────────────────────
    past = econ.get("past_week", [])
    themes = _detect_weekly_themes(past, news_items)
    fed_score   = themes.get("fed", 0)
    trade_score = themes.get("trade", 0)
    geo_score   = themes.get("geopolitics", 0)

    theme_parts = []
    if fed_score > 0:
        if treasury and treasury.get("yield_change_bps", 0) > 5:
            theme_parts.append(
                "Fed repricing was the dominant narrative: rising yields reflected a bond market"
                " pushing back on near-term rate-cut hopes, weighing on rate-sensitive sectors."
            )
        else:
            theme_parts.append(
                "Federal Reserve policy remained in focus, with investors watching for any shift"
                " in the rate-cut timeline."
            )
    if trade_score > 0:
        # Try to pull a specific headline
        trade_hl = ""
        for item in news_items:
            hl = item.get("headline", "")
            if any(kw in hl.lower() for kw in ["tariff", "section 301", "trade probe", "trade war"]):
                trade_hl = hl
                break
        if trade_hl:
            theme_parts.append(f"Trade policy added a layer of uncertainty — {trade_hl.rstrip('.')}.")
        else:
            theme_parts.append(
                "Trade policy tensions added a layer of uncertainty, with tariff headlines"
                " raising the cost outlook for import-dependent sectors."
            )
    if geo_score > 0:
        if oil and oil["weekly_pct"] > 2:
            theme_parts.append(
                f"Geopolitical risk was a direct market driver — Middle East conflict headlines"
                f" pushed WTI crude {oil['weekly_pct']:+.2f}% higher on the week to ${oil['close']:,.2f}/bbl,"
                f" raising fears of supply disruption through the Strait of Hormuz"
                f" and adding an inflationary wildcard to an already hawkish rate environment."
            )
        else:
            theme_parts.append(
                "Geopolitical risk remained elevated, with ongoing conflict headlines"
                " keeping a risk premium in oil and safe-haven assets."
            )

    if theme_parts:
        paras.append(" ".join(theme_parts))

    # ── Para 4: Economic data ─────────────────────────────────────────────────
    surprises = [e for e in past if e.get("surprise") in ("above", "below")]

    if surprises:
        data_lines = []
        for e in surprises:
            name     = e["event"]
            actual   = e["actual"]
            expected = e["expected"]
            unit     = e.get("unit", "")
            surprise = e["surprise"]
            direction = "beat" if surprise == "above" else "missed"
            data_lines.append(
                f"{name} {direction} expectations ({actual}{unit} vs. {expected}{unit} forecast)"
            )

        para_data = "On the economic data front, " + "; ".join(data_lines) + "."

        # Add so-what commentary
        has_hot_cpi     = any("cpi" in e["event"].lower() and e["surprise"] == "above" for e in surprises)
        has_hot_ppi     = any("ppi" in e["event"].lower() and e["surprise"] == "above" for e in surprises)
        has_hot_pce     = any("pce" in e["event"].lower() and e["surprise"] == "above" for e in surprises)
        has_strong_cons = any("confidence" in e["event"].lower() and e["surprise"] == "above" for e in surprises)
        has_weak_gdp    = any("gdp" in e["event"].lower() and e["surprise"] == "below" for e in surprises)

        if (has_hot_cpi or has_hot_ppi or has_hot_pce) and has_strong_cons:
            para_data += (
                " The combination of hot inflation prints and resilient consumer sentiment"
                " reinforces a higher-for-longer rate outlook — the Fed has little incentive"
                " to cut while both conditions hold."
            )
        elif has_hot_cpi or has_hot_ppi or has_hot_pce:
            para_data += (
                " Hotter-than-expected inflation data reduces the probability of near-term"
                " rate cuts, keeping pressure on rate-sensitive assets."
            )
        elif has_weak_gdp:
            para_data += (
                " Weaker-than-expected growth data shifts the risk calculus toward defensives"
                " and raises the prospect of earlier Fed action."
            )
        elif has_strong_cons:
            para_data += (
                " Strong consumer data suggests household spending remains resilient,"
                " supportive of consumer-facing sectors."
            )

        paras.append(para_data)
    else:
        paras.append(
            "The economic calendar was quiet this week, with no major data surprises"
            " to shift the macro narrative."
        )

    # ── Para 5: Look-ahead ────────────────────────────────────────────────────
    upcoming  = econ.get("upcoming_week", [])
    high_next = [e for e in upcoming if e.get("importance", 0) >= 3]
    med_next  = [e for e in upcoming if e.get("importance", 0) == 2]

    if high_next:
        high_names = [e["event"] for e in high_next]
        # Build specific commentary for known high-impact events
        watch_parts = []
        has_cpi = any("cpi" in n.lower() for n in high_names)
        has_pce = any("pce" in n.lower() for n in high_names)
        has_gdp = any("gdp" in n.lower() for n in high_names)
        has_nfp = any("nonfarm" in n.lower() or "payroll" in n.lower() for n in high_names)
        has_ppi = any("ppi" in n.lower() for n in high_names)
        has_fomc = any("fomc" in n.lower() for n in high_names)

        if has_fomc:
            watch_parts.append("the FOMC rate decision is the marquee event — markets will parse the statement and press conference for any shift in the rate-cut timeline. The dot plot update will reset expectations for the rest of 2026")
        if has_cpi:
            watch_parts.append("CPI will be the headline print — a hot number extends the higher-for-longer trade, a cool read revives rate-cut optimism")
        if has_pce:
            watch_parts.append("PCE (the Fed's preferred inflation gauge) will be closely watched for confirmation of the inflation trend")
        if has_gdp:
            watch_parts.append("GDP will test whether growth is holding up against the current rate environment")
        if has_nfp:
            watch_parts.append("the jobs report will set the tone on labor market resilience")
        if has_ppi and not has_cpi:
            watch_parts.append("PPI will offer an early read on pipeline inflation pressures")

        if watch_parts:
            joined = "; ".join(watch_parts)
            para_ahead = (
                f"Next week's calendar is heavy. "
                + joined[0].upper() + joined[1:]
                + ". Volatility around these releases is likely — position before the prints, not after."
            )
        else:
            para_ahead = (
                "Next week brings several high-importance releases: "
                + ", ".join(high_names)
                + ". These can move both equities and rates sharply; size positions accordingly."
            )

        if med_next:
            med_names = [e["event"] for e in med_next[:2]]
            para_ahead += f" Secondary data to watch: {', '.join(med_names)}."

        paras.append(para_ahead)
    elif med_next:
        med_names = [e["event"] for e in med_next]
        paras.append(
            f"Next week's calendar is lighter, with {', '.join(med_names)} the notable releases."
            " A quieter data week is a good opportunity to review allocations and rebalance."
        )
    else:
        paras.append(
            "Next week's calendar is light — a good time to review positions"
            " and rebalance rather than react to noise."
        )

    return "\n\n".join(paras)


def _detect_weekly_themes(past_events, news_items=None):
    """Return {theme: score} by scanning event names and news headlines."""
    all_text = " ".join([
        item.get("headline", "") + " " + item.get("summary", "")
        for item in (news_items or [])
    ] + [e.get("event", "") for e in (past_events or [])]).lower()

    return {
        "fed": sum(1 for kw in [
            "rate cut", "fed ", "fomc", "hawkish", "dovish", "rate hike",
            "monetary policy", "interest rate", "rate-cut", "cuts are fading",
            "cut expectations",
        ] if kw in all_text),
        "trade": sum(1 for kw in [
            "tariff", "trade war", "section 301", "forced labor",
            "import duty", "trade probe", "sanction", "trade tension",
            "trade practice",
        ] if kw in all_text),
        "geopolitics": sum(1 for kw in [
            "war", "iran", "israel", "ukraine", "geopolit",
            "conflict", "missile", "escalat", "military", "middle east",
        ] if kw in all_text),
        "earnings": sum(1 for kw in [
            "earnings", "eps beat", "revenue miss", "guidance",
            "quarterly results", "beat estimates",
        ] if kw in all_text),
    }


def _build_weekly_cross_indicator_para(index_data, past_events, news_items=None):
    """Return a paragraph connecting the week's dominant theme to cross-indicator signals."""
    sp       = next((i for i in index_data if "S&P" in i["name"]), None)
    nasdaq   = next((i for i in index_data if "Nasdaq" in i["name"]), None)
    russell  = next((i for i in index_data if "Russell" in i["name"]), None)
    treasury = next((i for i in index_data if "Treasury" in i["name"]), None)
    gold     = next((i for i in index_data if i["name"] == "Gold"), None)
    oil      = next((i for i in index_data if "Crude" in i["name"] or "WTI" in i["name"]), None)

    sp_pct    = sp["weekly_pct"]                   if sp       else None
    tsy_bps   = treasury.get("yield_change_bps")   if treasury else None
    tsy_close = treasury.get("close")              if treasury else None
    gold_pct  = gold["weekly_pct"]                 if gold     else None
    oil_pct   = oil["weekly_pct"]                  if oil      else None
    oil_close = oil["close"]                        if oil      else None

    themes          = _detect_weekly_themes(past_events, news_items)
    fed_prominent   = themes.get("fed", 0) > 0
    trade_prominent = themes.get("trade", 0) > 0
    geo_prominent   = themes.get("geopolitics", 0) > 0

    parts = []

    # ── Yield + equity connection ──────────────────────────────────────────────
    if tsy_bps is not None and abs(tsy_bps) >= 5 and tsy_close is not None:
        bps = round(abs(tsy_bps))
        if tsy_bps > 0 and sp_pct is not None and sp_pct < 0:
            if fed_prominent:
                lead = (
                    f"**The bond market is repricing the Fed.** The 10-year yield climbed {bps} bps "
                    f"over the week to {tsy_close:.2f}%, signalling that rate-cut expectations are fading. "
                    f"Higher yields at current levels compress equity valuations, particularly growth and small caps"
                )
                if nasdaq and russell:
                    lead += (
                        f" — which is why the Nasdaq ({nasdaq['weekly_pct']:+.2f}%) "
                        f"and Russell ({russell['weekly_pct']:+.2f}%) lagged the broader index."
                    )
                else:
                    lead += "."
                parts.append(lead)
            else:
                parts.append(
                    f"**Bond yields climbed {bps} bps to {tsy_close:.2f}% over the week**, "
                    f"making it harder to justify equity valuations — particularly in growth and small caps."
                )
        elif tsy_bps < 0 and sp_pct is not None and sp_pct < 0:
            parts.append(
                f"**Bond yields fell {bps} bps to {tsy_close:.2f}%** — a flight-to-safety "
                f"signal that reinforces the risk-off read across the week."
            )
        elif tsy_bps > 0 and sp_pct is not None and sp_pct > 0:
            parts.append(
                f"**Bond yields rose {bps} bps to {tsy_close:.2f}%** alongside stocks — "
                f"a sign of growth optimism, not inflation fear."
            )
        elif tsy_bps < 0:
            parts.append(
                f"**Bond yields fell {bps} bps to {tsy_close:.2f}%** — falling yields "
                f"typically support growth stocks and bond prices."
            )

    # ── Trade / geopolitics ────────────────────────────────────────────────────
    if trade_prominent or geo_prominent:
        trade_headline = ""
        geo_context    = ""
        for item in (news_items or []):
            hl_lower = item.get("headline", "").lower()
            if not trade_headline and any(
                kw in hl_lower for kw in ["section 301", "tariff", "forced labor", "trade probe"]
            ):
                trade_headline = item.get("headline", "")
            if not geo_context and any(
                kw in hl_lower for kw in ["iran", "israel", "war", "middle east"]
            ):
                geo_context = "Iran-Israel war tensions"

        if trade_headline:
            risk_para = f"**Trade risk added fuel this week.** {trade_headline}."
            if geo_context:
                risk_para += (
                    f" Combined with ongoing {geo_context}, investors are pricing in "
                    f"more geopolitical premium."
                )
            if oil_pct is not None and oil_pct > 2:
                risk_para += (
                    f" WTI crude reflected the tension directly, surging {oil_pct:+.2f}%"
                    f" to ${oil_close:,.2f}/bbl on supply disruption fears."
                )
            parts.append(risk_para)
        elif geo_prominent and geo_context:
            geo_para = (
                f"**Geopolitical risk remained elevated this week.** {geo_context.capitalize()} "
                f"continued to weigh on sentiment."
            )
            if oil_pct is not None and oil_pct > 2:
                geo_para += (
                    f" The risk premium showed up directly in energy prices — WTI crude"
                    f" climbed {oil_pct:+.2f}% to ${oil_close:,.2f}/bbl on supply disruption fears."
                )
            parts.append(geo_para)

    # ── Gold: counter-intuitive move ───────────────────────────────────────────
    if gold_pct is not None and sp_pct is not None and sp_pct < -0.5:
        if gold_pct < 0:
            dollar_driver = "tariff-driven " if trade_prominent else ""
            gold_note = (
                f"Worth noting: gold fell {abs(gold_pct):.2f}% despite the equity selloff — "
                f"a sign the dollar's {dollar_driver}strength is the dominant force, "
                f"not a simple flight to safety."
            )
            if parts:
                parts[-1] = parts[-1].rstrip(".") + ". " + gold_note
            else:
                parts.append(gold_note)
        elif gold_pct > 0.5:
            parts.append(
                f"Gold climbed {gold_pct:.2f}% alongside the weekly equity selloff — "
                f"investors are rotating into safe havens, amplifying the risk-off signal."
            )

    return "\n\n".join(parts)


def _build_next_week_binary_para(upcoming_events):
    """Frame next week's high-importance events as binary if/then outcomes."""
    high_next = [e for e in upcoming_events if e.get("importance", 0) >= 3]
    if not high_next:
        return ""

    event_names       = [e.get("event", "") for e in high_next]
    event_names_lower = [n.lower() for n in event_names]

    has_cpi = any("cpi" in n for n in event_names_lower)
    has_gdp = any("gdp" in n for n in event_names_lower)
    has_pce = any("pce" in n for n in event_names_lower)
    has_nfp = any(
        "nonfarm" in n or "non-farm" in n or "payroll" in n
        for n in event_names_lower
    )

    if has_gdp and has_pce:
        gdp_name = next((n for n in event_names if "gdp" in n.lower()), "GDP")
        pce_name = next((n for n in event_names if "pce" in n.lower()), "PCE")
        return (
            f"**Next week is binary.** {gdp_name} and {pce_name} both land. "
            f"A weak {gdp_name} + hot {pce_name} would be a stagflation signal — "
            f"defensives (XLU, XLP) over growth. A strong {gdp_name} + tame {pce_name} "
            f"keeps the soft-landing narrative intact. Position before the prints, not after."
        )

    if has_cpi:
        cpi_name = next((n for n in event_names if "cpi" in n.lower()), "CPI")
        return (
            f"**{cpi_name} is the key print next week.** "
            f"A hot number pressures growth stocks and pushes yields higher — TIPS and defensives benefit. "
            f"A cool read revives rate-cut hopes and lifts long bonds and tech. "
            f"Be positioned before the release, not after."
        )

    if has_nfp:
        nfp_name = next(
            (n for n in event_names if "nonfarm" in n.lower() or "non-farm" in n.lower() or "payroll" in n.lower()),
            "Non-Farm Payrolls",
        )
        return (
            f"**{nfp_name} lands next week — the monthly jobs report.** "
            f"A strong print keeps the Fed on hold and supports risk-on positioning. "
            f"A weak number shifts sentiment toward earlier rate cuts — positive for bonds and rate-sensitive sectors. "
            f"Either way, be positioned before Friday's release."
        )

    if has_gdp:
        gdp_name = next((n for n in event_names if "gdp" in n.lower()), "GDP")
        return (
            f"**Watch {gdp_name} next week.** A weak print shifts sentiment toward defensives (XLU, XLP); "
            f"a strong beat supports risk-on positioning in cyclicals (XLY, XLI). "
            f"Position before the release."
        )

    names_str = " and ".join(event_names[:2])
    return (
        f"**Key events next week: {names_str}.** "
        f"These can move markets — particularly bonds and rate-sensitive sectors. "
        f"Be positioned before the releases, not after."
    )


def generate_plain_english_summary(index_data, econ, news_items=None):
    """Generate a plain-English 'What This Means' section for active investors.

    4 paragraphs: breadth → cross-indicator → event explanations → next-week binary.
    """
    if not index_data:
        return "Not enough data to summarize this week."

    if news_items is None:
        news_items = []

    lines = []

    sp      = next((i for i in index_data if "S&P" in i["name"]), None)
    nasdaq  = next((i for i in index_data if "Nasdaq" in i["name"]), None)
    dow     = next((i for i in index_data if "Dow" in i["name"]), None)
    russell = next((i for i in index_data if "Russell" in i["name"]), None)
    usd     = next((i for i in index_data if i["name"] == "USD Index"), None)
    oil     = next((i for i in index_data if "Crude" in i["name"] or "WTI" in i["name"]), None)

    # ── Para 1: Breadth ───────────────────────────────────────────────────────
    if sp:
        pct         = sp["weekly_pct"]
        dollar_move = abs(pct) * 100  # per $10,000 portfolio

        equity_companions = [i for i in [nasdaq, dow, russell] if i]
        all_down = pct < 0 and all(c["weekly_pct"] < 0 for c in equity_companions)
        all_up   = pct > 0 and all(c["weekly_pct"] > 0 for c in equity_companions)

        if pct < -1.0 and all_down and equity_companions:
            comp_strs = []
            for idx in [russell, nasdaq, dow]:
                if idx:
                    label = {
                        "Russell 2000": "small caps (Russell 2000",
                        "Nasdaq":       "tech (Nasdaq",
                        "Dow Jones":    "blue chips (Dow",
                    }.get(idx["name"], idx["name"])
                    comp_strs.append(f"{label} {idx['weekly_pct']:+.2f}%)")
            if comp_strs:
                breadth_para = (
                    f"**This week's selloff was broad and deep.** The S&P 500 dropped "
                    f"{abs(pct):.1f}%, but the story is in the width: "
                    f"{', '.join(comp_strs)} all fell together — this wasn't sector "
                    f"rotation, it was risk-off across the board. A $10,000 index "
                    f"portfolio lost roughly ${dollar_move:,.0f}."
                )
            else:
                breadth_para = (
                    f"**It was a rough week for stocks.** The S&P 500 dropped {abs(pct):.1f}%, "
                    f"meaning a $10,000 index portfolio lost about ${dollar_move:,.0f}."
                )
        elif pct < 0 and equity_companions:
            down_comps = [c for c in equity_companions if c["weekly_pct"] < 0]
            up_comps   = [c for c in equity_companions if c["weekly_pct"] > 0]
            if up_comps and down_comps:
                breadth_para = (
                    f"**This week's decline was narrow, not broad.** The S&P 500 slipped "
                    f"{abs(pct):.1f}%, but markets weren't in full retreat — some areas "
                    f"held up. This looks more like rotation than a broad risk-off move."
                )
            else:
                breadth_para = (
                    f"**Stocks pulled back modestly this week.** The S&P 500 lost {abs(pct):.1f}% "
                    f"— a ${dollar_move:,.0f} hit on a $10,000 portfolio, nothing dramatic."
                )
        elif pct > 1.0 and all_up and equity_companions:
            comp_strs = []
            for idx in [nasdaq, dow]:
                if idx:
                    comp_strs.append(f"{idx['name']} {idx['weekly_pct']:+.2f}%")
            advance = f" with {' and '.join(comp_strs)} joining the advance" if comp_strs else ""
            breadth_para = (
                f"**This week's rally was broad-based.** The S&P 500 gained {pct:.1f}%"
                f"{advance} — a clean risk-on week. A $10,000 portfolio added "
                f"roughly ${dollar_move:,.0f}."
            )
        elif pct > 0:
            breadth_para = (
                f"**Stocks edged higher this week.** The S&P 500 was up {pct:+.1f}% "
                f"— a quiet positive week, nothing dramatic."
            )
        else:
            breadth_para = (
                f"**Stocks slipped modestly this week.** The S&P 500 lost {abs(pct):.1f}% "
                f"— a routine dip, not a panic."
            )

        if usd and abs(usd["weekly_pct"]) >= 0.4:
            if usd["weekly_pct"] > 0:
                breadth_para += (
                    f" The dollar also strengthened {usd['weekly_pct']:+.1f}% — a quiet headwind "
                    f"if you hold international ETFs, as foreign gains get partially erased when converted back to USD."
                )
            else:
                breadth_para += (
                    f" The dollar weakened {abs(usd['weekly_pct']):.1f}% — a tailwind for international ETFs "
                    f"and commodities like gold."
                )

        lines.append(breadth_para)

    # ── Para 2: Cross-indicator narrative ─────────────────────────────────────
    past = econ.get("past_week", [])
    cross_para = _build_weekly_cross_indicator_para(index_data, past, news_items)
    if cross_para:
        lines.append(cross_para)

    # ── Para 3: Economic event explanations (flowing prose) ───────────────────
    data_paras = []

    for ev in past:
        name      = ev.get("event", "")
        surprise  = ev.get("surprise", "neutral")
        actual    = ev.get("actual", "--")
        unit      = ev.get("unit", "")
        name_lower = name.lower()

        if "consumer confidence" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"Consumer Confidence came in at {actual} — higher than expected. "
                    f"Everyday Americans feel relatively okay about their jobs and finances, "
                    f"which tends to support continued spending."
                )
            elif surprise == "below":
                data_paras.append(
                    f"Consumer Confidence disappointed at {actual}. "
                    f"People are feeling less optimistic about the economy — when confidence drops, "
                    f"spending usually follows."
                )

        elif "ppi" in name_lower or "producer price" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"The Producer Price Index — what businesses pay for their inputs — "
                    f"came in hotter than expected at {actual}{unit}. "
                    f"When businesses pay more to make things, they eventually pass those costs on to consumers. "
                    f"It also signals the Fed probably won't be cutting rates anytime soon."
                )
            elif surprise == "below":
                data_paras.append(
                    f"Producer prices came in cooler than expected — good news on the inflation front. "
                    f"Lower input costs for businesses can eventually mean lower prices for consumers "
                    f"and gives the Fed more room to think about cutting rates."
                )

        elif "pce" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"The PCE inflation reading — the Fed's preferred measure — "
                    f"came in hotter than expected at {actual}{unit}. "
                    f"This tells the Fed that inflation isn't beaten yet, "
                    f"making interest rate cuts less likely and keeping pressure on stocks."
                )
            elif surprise == "below":
                data_paras.append(
                    f"PCE inflation — the Fed's preferred gauge — cooled more than expected. "
                    f"That's the kind of data the Fed needs to see before cutting rates — "
                    f"good news for growth stocks and bond prices."
                )

        elif "core cpi" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"Core CPI — inflation stripping out food and energy — came in hotter than expected at {actual}{unit}. "
                    f"Sticky core inflation is the Fed's primary concern; this makes near-term rate cuts less likely."
                )
            elif surprise == "below":
                data_paras.append(
                    f"Core CPI — the Fed's cleanest read on underlying inflation — came in softer than expected at {actual}{unit}. "
                    f"This is the most encouraging kind of disinflation: not just cheaper gas, but genuine easing of "
                    f"underlying price pressures. It gives the Fed more room to eventually cut rates."
                )

        elif "cpi" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"Inflation (CPI) ran hotter than expected at {actual}{unit}. "
                    f"Higher-than-expected inflation means the Fed is less likely to cut interest rates soon. "
                    f"Rate cuts are generally good for stocks — so this delays that tailwind."
                )
            elif surprise == "below":
                data_paras.append(
                    f"Headline CPI came in cooler than expected at {actual}{unit}. "
                    f"Progress on inflation gives the Fed more room to cut rates, "
                    f"which tends to be a positive for both stocks and bonds."
                )

        elif "gdp" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"GDP — the broadest measure of economic output — beat expectations at {actual}{unit}. "
                    f"A stronger economy generally means better corporate earnings ahead."
                )
            elif surprise == "below":
                data_paras.append(
                    f"GDP growth came in below expectations at {actual}{unit}. "
                    f"The economy grew, but more slowly than hoped. "
                    f"Defensives (utilities, consumer staples) tend to hold up better in slower-growth environments."
                )

        elif "tariff" in name_lower or "scotus" in name_lower:
            data_paras.append(
                f"The big non-data story this week was trade policy. "
                f"Tariffs raise costs for U.S. companies that import goods — that pressure can squeeze profit margins "
                f"and eventually show up as higher prices, adding uncertainty the market doesn't love."
            )

        elif "durable goods" in name_lower:
            if surprise == "above":
                data_paras.append(
                    f"Durable goods orders — big purchases like machinery and equipment — beat expectations. "
                    f"Businesses are still investing, which is a healthy economic signal."
                )
            elif surprise == "below":
                data_paras.append(
                    f"Durable goods orders disappointed. Businesses are pulling back on big-ticket purchases "
                    f"— a caution signal for the industrial and manufacturing sector."
                )

        elif "services pmi" in name_lower or "flash services" in name_lower:
            if surprise == "below" and actual != "--":
                try:
                    val = float(actual)
                    if val < 50:
                        data_paras.append(
                            f"The services sector — which drives most of the U.S. economy — "
                            f"unexpectedly contracted (PMI of {actual}, below the 50 line that separates "
                            f"growth from contraction). That's a meaningful warning sign."
                        )
                    else:
                        data_paras.append(
                            f"Services activity expanded but came in softer than expected at {actual}. "
                            f"The services sector is still growing but losing momentum."
                        )
                except (ValueError, TypeError):
                    pass

        elif "manufacturing pmi" in name_lower or "flash manufacturing" in name_lower:
            if actual != "--":
                try:
                    val = float(actual)
                    if val > 50:
                        data_paras.append(
                            f"Manufacturing activity expanded this week (PMI of {actual}). "
                            f"Factories are busier — generally positive for industrial stocks."
                        )
                    else:
                        data_paras.append(
                            f"Manufacturing activity contracted (PMI of {actual}, below 50). "
                            f"A slowdown in factory output can signal broader economic weakness ahead."
                        )
                except (ValueError, TypeError):
                    pass

    if data_paras:
        lines.append(" ".join(data_paras))

    # ── Para 4: Next-week binary framing ──────────────────────────────────────
    upcoming = econ.get("upcoming_week", [])
    binary_para = _build_next_week_binary_para(upcoming)
    if binary_para:
        lines.append(binary_para)

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

    fomc_tip_added = False
    for event in upcoming:
        name = event.get("event", "").lower()
        if "fomc" in name and not fomc_tip_added:
            label = "FOMC Rate Decision" if "rate decision" in name else "FOMC meeting"
            tips.append(
                f"{label} on {{date}}"
                " -- expect volatility around the announcement and press conference. "
                "Consider trimming position sizes or hedging with VIX calls.".format(**event)
            )
            fomc_tip_added = True
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


def build_template_context(index_data, econ, date_str, daybreak_context=None):
    """Assemble the full context dict for the Jinja2 template.

    Args:
        index_data: List from process_index_data.
        econ: Raw econ calendar dict.
        date_str: The newsletter date (YYYY-MM-DD).
        daybreak_context: Optional dict from _load_week_daybreak_data with
            news_items and week_events aggregated from daily daybreak fixtures.

    Returns:
        Dict ready for Jinja2 rendering.
    """
    tips = generate_positioning_tips(econ, index_data)
    news_items = (daybreak_context or {}).get("news_items", [])
    narrative = generate_narrative(index_data, econ, news_items=news_items)
    plain_summary = generate_plain_english_summary(index_data, econ, news_items=news_items)

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
