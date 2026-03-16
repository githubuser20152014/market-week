"""Process raw daybreak data into newsletter-ready content."""


def process_market_news(raw_news: list) -> list:
    """Pass through news items, truncating long summaries."""
    out = []
    for item in raw_news:
        out.append({
            "headline":  item.get("headline", ""),
            "source":    item.get("source", ""),
            "published": item.get("published", ""),
            "url":       item.get("url", ""),
            "summary":   item.get("summary", "")[:180],
        })
    return out


def process_us_close(raw: dict) -> list:
    """Convert raw us_close dict to a sorted list (best daily_pct first).

    Returns:
        List of dicts with keys: name, symbol, close, daily_pct,
        is_yield, yield_change_bps (last two only for treasury entries).
    """
    results = []
    for name, info in raw.items():
        daily_pct = info.get("daily_pct")
        entry = {
            "name":      name,
            "symbol":    info.get("symbol", ""),
            "close":     info.get("close"),
            "daily_pct": daily_pct,
            "table":     info.get("table", True),
        }
        if info.get("is_yield"):
            entry["is_yield"]         = True
            entry["yield_change_bps"] = info.get("yield_change_bps")
        results.append(entry)

    results.sort(
        key=lambda x: (x["daily_pct"] is None, -(x["daily_pct"] or 0))
    )
    return results


def process_intl_overnight(raw: dict) -> list:
    """Convert raw intl_overnight dict to a list: APAC first, then Europe.

    Returns:
        List of dicts with keys: name, symbol, region, status,
        close, daily_pct, session_note.
    """
    apac   = []
    europe = []
    other  = []

    for name, info in raw.items():
        entry = {
            "name":         name,
            "symbol":       info.get("symbol", ""),
            "region":       info.get("region", ""),
            "status":       info.get("status", "closed"),
            "close":        info.get("close"),
            "daily_pct":    info.get("daily_pct"),
            "session_note": info.get("session_note", ""),
        }
        region = info.get("region", "")
        if region == "Asia-Pacific":
            apac.append(entry)
        elif region == "Europe":
            europe.append(entry)
        else:
            other.append(entry)

    return apac + europe + other


def process_fx(raw: dict) -> list:
    """Convert raw fx dict to a list."""
    results = []
    for name, info in raw.items():
        results.append({
            "name":       name,
            "symbol":     info.get("symbol", ""),
            "rate":       info.get("rate"),
            "prev_close": info.get("prev_close"),
            "daily_pct":  info.get("daily_pct"),
        })
    return results


def process_futures(raw: dict) -> list:
    """Convert raw futures dict to a list."""
    results = []
    for name, info in raw.items():
        results.append({
            "name":       name,
            "symbol":     info.get("symbol", ""),
            "price":      info.get("price"),
            "prev_close": info.get("prev_close"),
            "daily_pct":  info.get("daily_pct"),
        })
    return results


# ── Narrative ─────────────────────────────────────────────────────────────────

def generate_daybreak_narrative(us_indices: list, intl_indices: list,
                                 fx: list, futures: list) -> str:
    """Generate a 2-paragraph morning brief narrative.

    Para 1: US close direction + FX/gold/treasury signals.
    Para 2: APAC overnight + European early session + futures pre-market signal.
    """
    # ── Para 1: US close ─────────────────────────────────────────────────────
    sp      = next((i for i in us_indices if "S&P" in i["name"]), None)
    nasdaq  = next((i for i in us_indices if "Nasdaq" in i["name"]), None)
    gold    = next((i for i in us_indices if i["name"] == "Gold"), None)
    treasury = next((i for i in us_indices if "Treasury" in i["name"]), None)
    eur_usd = next((f for f in fx if "EUR" in f["name"]), None)
    oil     = next((i for i in us_indices if "WTI" in i["name"] or "Crude" in i["name"]), None)

    if sp and sp["daily_pct"] is not None:
        pct = sp["daily_pct"]
        if pct > 1:
            tone = "US stocks rallied"
        elif pct > 0:
            tone = "US stocks edged higher"
        elif pct > -1:
            tone = "US stocks slipped modestly"
        else:
            tone = "US stocks fell sharply"
        sp_close_str = f" {sp['close']:,.2f}" if sp.get("close") else ""
        para1 = f"At market close, {tone} — the S&P 500 ended{sp_close_str} ({pct:+.2f}%)"
        if nasdaq and nasdaq["daily_pct"] is not None:
            nq_close_str = f" {nasdaq['close']:,.2f}" if nasdaq.get("close") else ""
            para1 += f", while the Nasdaq finished{nq_close_str} ({nasdaq['daily_pct']:+.2f}%)"
        para1 += "."
    else:
        para1 = "US market data unavailable for yesterday's session."

    safe_notes = []
    if gold and gold["daily_pct"] is not None:
        direction = "climbed" if gold["daily_pct"] > 0 else "fell"
        safe_notes.append(
            f"Gold {direction} {abs(gold['daily_pct']):.2f}% to "
            f"${gold['close']:,.2f}" if gold["close"] else
            f"Gold {direction} {abs(gold['daily_pct']):.2f}%"
        )
    if treasury and treasury.get("yield_change_bps") is not None:
        bps = treasury["yield_change_bps"]
        if round(abs(bps)) == 0:
            safe_notes.append(f"the 10-year Treasury yield held flat at {treasury['close']:.2f}%")
        else:
            direction = "rose" if bps > 0 else "fell"
            safe_notes.append(
                f"the 10-year Treasury yield {direction} {round(abs(bps)):.0f} bps "
                f"to {treasury['close']:.2f}%"
            )
    if eur_usd and eur_usd["daily_pct"] is not None:
        direction = "strengthened" if eur_usd["daily_pct"] < 0 else "softened"
        safe_notes.append(
            f"the dollar {direction} (EUR/USD {eur_usd['rate']:.4f})"
            if eur_usd["rate"] else
            f"the dollar {direction} against the euro"
        )
    if safe_notes:
        if len(safe_notes) == 1:
            joined = safe_notes[0]
        elif len(safe_notes) == 2:
            joined = f"{safe_notes[0]}, while {safe_notes[1]}"
        else:
            joined = ", ".join(safe_notes[:-1]) + f", and {safe_notes[-1]}"
        para1 += " On the safe-haven front, " + joined + "."

    if oil and oil["daily_pct"] is not None:
        direction = "rose" if oil["daily_pct"] > 0 else "fell"
        oil_str = (
            f"WTI crude {direction} {abs(oil['daily_pct']):.2f}% to ${oil['close']:,.2f}/bbl."
            if oil["close"] else
            f"WTI crude {direction} {abs(oil['daily_pct']):.2f}%."
        )
        para1 += f" {oil_str}"

    # ── Para 2: Overnight + futures ───────────────────────────────────────────
    apac_entries   = [i for i in intl_indices if i["region"] == "Asia-Pacific"
                      and i["daily_pct"] is not None]
    europe_entries = [i for i in intl_indices if i["region"] == "Europe"
                      and i["daily_pct"] is not None]

    para2_parts = []
    if apac_entries:
        apac_up   = sum(1 for i in apac_entries if i["daily_pct"] >= 0)
        apac_down = len(apac_entries) - apac_up
        if apac_up == len(apac_entries):
            apac_tone = "APAC markets closed broadly higher overnight"
        elif apac_down == len(apac_entries):
            apac_tone = "APAC markets closed broadly lower overnight"
        else:
            apac_tone = "APAC markets were mixed overnight"

        best_apac  = max(apac_entries, key=lambda x: x["daily_pct"])
        worst_apac = min(apac_entries, key=lambda x: x["daily_pct"])
        if best_apac["name"] != worst_apac["name"]:
            apac_tone += (
                f", with {best_apac['name']} leading at {best_apac['daily_pct']:+.2f}% "
                f"and {worst_apac['name']} lagging at {worst_apac['daily_pct']:+.2f}%"
            )
        para2_parts.append(apac_tone + ".")

    if europe_entries:
        eu_up   = sum(1 for i in europe_entries if i["daily_pct"] >= 0)
        eu_down = len(europe_entries) - eu_up
        partial = any(i["status"] == "partial" for i in europe_entries)
        eu_label = "European markets are trading" if partial else "European markets closed"
        if eu_up == len(europe_entries):
            eu_tone = f"{eu_label} higher"
        elif eu_down == len(europe_entries):
            eu_tone = f"{eu_label} lower"
        else:
            eu_tone = f"{eu_label} mixed"
        para2_parts.append(eu_tone + ".")

    # Futures direction
    fut_with_data = [f for f in futures if f["daily_pct"] is not None]
    if fut_with_data:
        all_green = all(f["daily_pct"] >= 0 for f in fut_with_data)
        all_red   = all(f["daily_pct"] < 0  for f in fut_with_data)
        if all_green:
            para2_parts.append(
                "US futures are pointing to a positive open across the board."
            )
        elif all_red:
            para2_parts.append(
                "US futures are signalling a cautious open — all three major contracts "
                "are in the red heading into the session."
            )
        else:
            para2_parts.append(
                "US futures are sending a mixed signal ahead of the open."
            )

    para2 = " ".join(para2_parts) if para2_parts else \
        "Overnight market data unavailable."

    return f"{para1}\n\n{para2}"


# ── Plain-English Summary ─────────────────────────────────────────────────────

def _detect_dominant_themes(news_items: list, yesterday_events: list) -> dict:
    """Return {theme: score} from scanning headlines and event names."""
    all_text = " ".join([
        item.get("headline", "") + " " + item.get("summary", "")
        for item in (news_items or [])
    ] + [e.get("event", "") for e in (yesterday_events or [])]).lower()

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


def _build_what_happened_para(sp, nasdaq, dow, russell, gold, treasury, usd, oil) -> str:
    """Para 1: Full session recap — equity breadth + cross-asset picture."""
    if not sp or sp.get("daily_pct") is None:
        return ""

    pct = sp["daily_pct"]

    # Tone
    if pct <= -2.0:
        tone = "Stocks sold off sharply yesterday"
    elif pct <= -1.0:
        tone = "Stocks declined meaningfully yesterday"
    elif pct < 0:
        tone = "Stocks pulled back modestly yesterday"
    elif pct >= 2.0:
        tone = "Stocks rallied strongly yesterday"
    elif pct >= 1.0:
        tone = "Stocks had a solid session yesterday"
    else:
        tone = "Stocks edged higher yesterday"

    sp_close_str = f" {sp['close']:,.2f}" if sp.get("close") else ""
    sentence = f"**{tone}.** The S&P 500 closed{sp_close_str} ({pct:+.2f}%)"

    companions = []
    for idx in [nasdaq, dow, russell]:
        if idx and idx.get("daily_pct") is not None:
            label = {"Nasdaq": "Nasdaq", "Dow Jones": "Dow", "Russell 2000": "Russell 2000"}.get(idx["name"], idx["name"])
            close_str = f" {idx['close']:,.2f}" if idx.get("close") else ""
            companions.append(f"the {label}{close_str} ({idx['daily_pct']:+.2f}%)")
    if companions:
        sentence += ", " + ", ".join(companions)
    sentence += "."

    # Breadth read
    comp_list = [idx for idx in [nasdaq, dow, russell] if idx and idx.get("daily_pct") is not None]
    if comp_list:
        all_down = pct < 0 and all(c["daily_pct"] < 0 for c in comp_list)
        all_up   = pct > 0 and all(c["daily_pct"] > 0 for c in comp_list)
        if pct < 0 and all_down:
            sentence += " Selling was broad — all four major indices closed in the red."
        elif pct > 0 and all_up:
            sentence += " The advance was broad — all four major indices closed in the green."
        elif pct < 0:
            up_count = sum(1 for c in comp_list if c["daily_pct"] > 0)
            if up_count:
                sentence += (
                    f" Notably, {up_count} of the other major indices held positive —"
                    " this looks more like rotation than broad risk-off selling."
                )

    # Cross-asset
    cross = []
    if gold and gold.get("daily_pct") is not None:
        direction = "climbed" if gold["daily_pct"] > 0 else "fell"
        close_str = f" to ${gold['close']:,.2f}" if gold.get("close") else ""
        cross.append(f"Gold {direction} {abs(gold['daily_pct']):.2f}%{close_str}")
    if treasury and treasury.get("yield_change_bps") is not None:
        bps = round(treasury["yield_change_bps"])
        if bps == 0:
            cross.append(f"the 10-year Treasury yield held flat at {treasury['close']:.2f}%")
        elif bps > 0:
            cross.append(f"the 10-year Treasury yield rose {abs(bps)} bps to {treasury['close']:.2f}%")
        else:
            cross.append(f"the 10-year Treasury yield fell {abs(bps)} bps to {treasury['close']:.2f}%")
    if oil and oil.get("daily_pct") is not None:
        direction = "rose" if oil["daily_pct"] > 0 else "fell"
        close_str = f" to ${oil['close']:,.2f}/bbl" if oil.get("close") else ""
        cross.append(f"WTI crude {direction} {abs(oil['daily_pct']):.2f}%{close_str}")
    if usd and usd.get("daily_pct") is not None:
        direction = "strengthened" if usd["daily_pct"] > 0 else "weakened"
        cross.append(f"the dollar {direction} {abs(usd['daily_pct']):.2f}%")

    if cross:
        if len(cross) == 1:
            cross_str = cross[0]
        else:
            cross_str = ", ".join(cross[:-1]) + ", and " + cross[-1]
        sentence += f" On the cross-asset front: {cross_str}."

    return sentence


def _build_why_it_happened_para(sp, nasdaq, russell, treasury, gold, usd, oil,
                                 news_items, yesterday_events, themes) -> str:
    """Para 2: Why it happened — causal narrative linking news/data to price action."""
    sp_pct    = sp["daily_pct"]              if sp       and sp.get("daily_pct")      is not None else None
    tsy_bps   = treasury.get("yield_change_bps") if treasury else None
    tsy_close = treasury.get("close")        if treasury else None
    gold_pct  = gold["daily_pct"]            if gold     and gold.get("daily_pct")    is not None else None
    oil_close = oil.get("close")             if oil else None

    geo_score   = themes.get("geopolitics", 0)
    fed_score   = themes.get("fed", 0)
    trade_score = themes.get("trade", 0)

    # Pull the most relevant headline for each theme
    geo_headline   = ""
    trade_headline = ""
    for item in (news_items or []):
        hl       = item.get("headline", "")
        hl_lower = hl.lower()
        if not geo_headline and any(kw in hl_lower for kw in ["iran", "israel", "hormuz", "war", "military", "escalat"]):
            geo_headline = hl
        if not trade_headline and any(kw in hl_lower for kw in ["tariff", "trade", "sanction", "section 301"]):
            trade_headline = hl

    # Yesterday's data surprises
    econ_notes = []
    for event in (yesterday_events or []):
        name     = event.get("event", "")
        surprise = event.get("surprise", "")
        actual   = event.get("actual", "--")
        expected = event.get("expected", "--")
        unit     = event.get("unit", "")
        if surprise in ("above", "below") and name:
            direction = "came in hot" if surprise == "above" else "missed estimates"
            econ_notes.append(f"{name} {direction} ({actual}{unit} vs. {expected}{unit} expected)")

    parts = []

    # --- Dominant theme ---

    # Geopolitics-led
    if geo_score >= 2 and geo_headline:
        para = f"**Geopolitics was the session's dominant force.** {geo_headline}."
        if "hormuz" in geo_headline.lower() or ("oil" in geo_headline.lower() and oil_close and oil_close > 95):
            para += (
                " The Strait of Hormuz is the world's most important oil chokepoint —"
                " roughly 20% of global oil supply transits through it daily."
                " Any credible disruption threat moves energy markets and ripples through"
                " inflation expectations, transportation costs, and emerging-market currencies."
            )
        elif "iran" in geo_headline.lower() or "israel" in geo_headline.lower():
            para += (
                " Middle East escalation raises the geopolitical risk premium across"
                " oil, shipping, and global supply chains — even headlines that don't"
                " immediately disrupt flows move markets because investors reprice tail risk."
            )

        # Counter-intuitive gold move
        if gold_pct is not None and gold_pct < -0.3 and sp_pct is not None and sp_pct < 0:
            para += (
                f" A notable cross-asset signal: gold fell {abs(gold_pct):.2f}% despite the equity decline."
                " Normally, geopolitical stress pushes investors into gold."
                " When gold drops alongside stocks, it typically signals that the dollar"
                " is the real safe-haven destination — investors are buying USD, not bullion."
            )
            if tsy_bps is not None and abs(tsy_bps) < 3:
                para += (
                    f" The 10-year yield's near-flat move confirms there was no meaningful"
                    f" rotation into Treasuries either — the flight-to-safety trade went"
                    f" straight to cash and the dollar."
                )
        elif gold_pct is not None and gold_pct > 0.5 and sp_pct is not None and sp_pct < 0:
            para += (
                f" Gold's {gold_pct:.2f}% gain alongside the equity selloff strengthens"
                f" the risk-off read — investors are actively rotating into safe havens."
            )
        parts.append(para)

    # Fed-led
    elif fed_score >= 2:
        if tsy_bps is not None and tsy_bps > 3 and tsy_close is not None and sp_pct is not None and sp_pct < 0:
            para = (
                f"**The bond market is pricing out rate cuts.** Treasury yields climbed"
                f" {round(abs(tsy_bps))} bps to {tsy_close:.2f}% as investors reassessed"
                f" the timeline for Fed easing. Higher yields increase the discount rate"
                f" applied to future earnings — which compresses valuations, particularly"
                f" in growth and long-duration assets."
            )
            if nasdaq and nasdaq.get("daily_pct") is not None and nasdaq["daily_pct"] < (sp_pct or 0):
                para += (
                    f" That mechanism showed up clearly: the Nasdaq underperformed the S&P 500"
                    f" ({nasdaq['daily_pct']:+.2f}% vs. {sp_pct:+.2f}%), consistent with a"
                    f" yield-driven selloff hitting growth stocks hardest."
                )
            parts.append(para)
        else:
            parts.append(
                "**Fed expectations are in flux.** Rate-cut expectations continued to shift,"
                " creating uncertainty around the cost of capital and equity valuations."
            )

    # Trade-led
    elif trade_score >= 2 and trade_headline:
        para = f"**Trade policy risk drove the session.** {trade_headline}."
        if sp_pct is not None and sp_pct < 0:
            para += (
                " Tariff and trade-war headlines hit multinationals and supply-chain-heavy"
                " sectors disproportionately hard — companies with significant overseas"
                " revenue or production face margin compression that's hard to hedge."
            )
        parts.append(para)

    # Data-driven session
    elif econ_notes:
        note = econ_notes[0]
        para = f"**Economic data moved the needle yesterday.** {note}."
        if tsy_bps is not None and abs(tsy_bps) >= 3 and tsy_close is not None:
            direction = "higher" if tsy_bps > 0 else "lower"
            para += (
                f" Bond markets responded: the 10-year yield moved {direction}"
                f" {round(abs(tsy_bps))} bps to {tsy_close:.2f}%, which fed directly"
                f" into equity valuations through the discount-rate channel."
            )
        parts.append(para)

    # Light-catalyst session
    elif sp_pct is not None and abs(sp_pct) < 0.75:
        parts.append(
            "**It was a low-catalyst session.** No single data print or headline"
            " stood out as the driver — this looks like normal price discovery in a"
            " directionless tape. Low-conviction moves like this often reverse quickly"
            " once a clear catalyst re-enters the picture."
        )

    # Yield-driven (fallback)
    elif tsy_bps is not None and abs(tsy_bps) >= 4 and tsy_close is not None:
        direction = "climbed" if tsy_bps > 0 else "fell"
        parts.append(
            f"**Bond yields {direction} {round(abs(tsy_bps))} bps to {tsy_close:.2f}%.**"
            f" {'Rising yields compress equity valuations, particularly in growth and rate-sensitive sectors.' if tsy_bps > 0 else 'Falling yields reduce the competition bonds pose to equities and tend to support growth stocks.'}"
        )

    return "\n\n".join(parts)


def _build_investor_implications_para(sp, nasdaq, russell, treasury, gold, usd, oil,
                                       news_items, yesterday_events, themes) -> str:
    """Para 3: What it means for you — portfolio implications and ETF signals."""
    sp_pct    = sp["daily_pct"]    if sp       and sp.get("daily_pct")      is not None else None
    tsy_bps   = treasury.get("yield_change_bps") if treasury else None
    tsy_close = treasury.get("close")        if treasury else None
    gold_pct  = gold["daily_pct"]  if gold     and gold.get("daily_pct")    is not None else None
    usd_pct   = usd["daily_pct"]   if usd      and usd.get("daily_pct")     is not None else None
    oil_pct   = oil["daily_pct"]   if oil      and oil.get("daily_pct")     is not None else None
    oil_close = oil.get("close")   if oil else None

    geo_score   = themes.get("geopolitics", 0)
    trade_score = themes.get("trade", 0)
    fed_score   = themes.get("fed", 0)

    implications = []
    watch_items  = []

    # Dollar
    if usd_pct is not None and usd_pct > 0.3:
        implications.append(
            f"Dollar strength ({usd_pct:+.2f}%) is a headwind for multinationals"
            f" — many S&P 500 large caps collect revenue in foreign currencies but report in USD."
            f" It also pressures commodities priced in dollars; GLD and broad commodity ETFs (DJP)"
            f" face a direct drag when the dollar strengthens."
        )
    elif usd_pct is not None and usd_pct < -0.3:
        implications.append(
            f"Dollar weakness ({usd_pct:+.2f}%) is a tailwind for international equities"
            f" and commodity ETFs — EM-focused funds (EEM, VWO) and commodities (GLD, DJP)"
            f" tend to benefit when the dollar softens."
        )

    # Oil above $100
    if oil_close is not None and oil_close > 100:
        watch_items.append("oil — above $100/bbl starts to pressure consumer spending and complicate the Fed's inflation picture")
        implications.append(
            f"With WTI crude above $100/bbl, energy costs are becoming a macro drag."
            f" Sustained elevated oil raises input costs across the supply chain, keeps"
            f" headline CPI sticky, and makes the Fed's path to rate cuts harder to justify."
            f" Energy ETFs (XLE) are in focus, but be cautious: geopolitical oil spikes"
            f" can reverse fast if the diplomatic situation de-escalates."
        )
    elif oil_pct is not None and oil_pct < -1.5:
        implications.append(
            f"Oil's {abs(oil_pct):.2f}% decline is a quiet tailwind for consumer-facing"
            f" sectors — lower energy costs flow into margins for transportation (XTN),"
            f" retail (XRT), and airlines."
        )

    # Yield implications
    if tsy_bps is not None and tsy_bps > 4 and tsy_close is not None:
        watch_items.append(f"the 10-year yield — further moves above {tsy_close:.2f}% would widen the pressure on valuations")
        implications.append(
            f"At {tsy_close:.2f}%, the 10-year yield is meaningful competition for equities"
            f" as an income source. Growth-heavy portfolios (QQQ) are most exposed to further"
            f" yield increases. If yields stay elevated, tilting toward value and dividend-payers"
            f" (VTV, DVY, SCHD) has historically held up better in high-rate environments."
        )
    elif tsy_bps is not None and tsy_bps < -4 and tsy_close is not None:
        implications.append(
            f"Falling yields ({tsy_close:.2f}% now) reduce bond competition for equity capital"
            f" and tend to lift rate-sensitive sectors: REITs (VNQ), utilities (XLU),"
            f" and long-duration growth stocks. Consider whether the yield decline reflects"
            f" growth fears (negative for cyclicals) or simply easing inflation (more benign)."
        )

    # Geopolitical premium flag
    if geo_score >= 2:
        watch_items.append("geopolitical headlines — any escalation or de-escalation will move oil, FX, and risk sentiment quickly")

    if gold_pct is not None and gold_pct < -0.5 and sp_pct is not None and sp_pct < 0:
        watch_items.append("gold — if risk-off sentiment re-intensifies, gold could recover sharply as the safe-haven trade catches up")

    # Fallback for quiet session
    if not implications:
        if sp_pct is not None and abs(sp_pct) < 0.5:
            implications.append(
                "Yesterday's session was quiet — no major allocation changes are warranted."
                " Modest moves without a clear catalyst are noise, not signal."
            )
        elif sp_pct is not None and sp_pct < 0:
            implications.append(
                "For diversified ETF holders, a sub-1% pullback doesn't call for a defensive"
                " pivot. Broad index dips at this magnitude are within normal volatility."
                " Hold course and watch whether today's open confirms or reverses the direction."
            )

    parts = []
    if implications:
        lead = "**For diversified ETF holders, here's what to watch:**"
        parts.append(lead + " " + " ".join(implications))
    if watch_items:
        parts.append("**Keep a close eye on:** " + "; ".join(watch_items) + ".")

    return "\n\n".join(parts)


def _build_going_into_today_para(futures, intl_indices, today_events, sp) -> str:
    """Para 4: Going into today — pre-market signal, overnight context, and today's catalysts."""
    parts = []

    fut_with_data = [f for f in futures if f.get("daily_pct") is not None]
    equity_futs   = [f for f in fut_with_data if any(kw in f.get("name", "") for kw in ["S&P", "Nasdaq", "Dow"])]
    sp_pct        = sp["daily_pct"] if sp and sp.get("daily_pct") is not None else None

    # Pre-market futures
    if equity_futs:
        all_green = all(f["daily_pct"] >= 0 for f in equity_futs)
        all_red   = all(f["daily_pct"] < 0  for f in equity_futs)

        sp_fut  = next((f for f in equity_futs if "S&P" in f.get("name", "")), None)
        nq_fut  = next((f for f in equity_futs if "Nasdaq" in f.get("name", "")), None)
        dow_fut = next((f for f in equity_futs if "Dow" in f.get("name", "")), None)

        fut_strs = []
        for f in [sp_fut, nq_fut, dow_fut]:
            if f:
                name = f.get("name", "").replace(" Futures", "")
                fut_strs.append(f"{name} {f['daily_pct']:+.2f}%")
        fut_detail = " | ".join(fut_strs) if fut_strs else ""

        if all_green:
            open_call = (
                f"**Pre-market is pointing to a positive open** ({fut_detail})."
            )
            if sp_pct and sp_pct < 0:
                open_call += (
                    " The market is treating yesterday's decline as a dip, not a trend."
                    " Watch whether buyers follow through with conviction once cash markets"
                    " open, or whether early strength fades."
                )
            else:
                open_call += (
                    " Futures are extending yesterday's gains — risk-on momentum is intact."
                    " Watch for potential overextension if there's no fresh catalyst."
                )
        elif all_red:
            open_call = (
                f"**Pre-market is signalling caution** ({fut_detail})."
            )
            if sp_pct and sp_pct < 0:
                open_call += (
                    " Sellers appear to be extending yesterday's weakness."
                    " Watch whether buyers step in at key support levels or if the selling accelerates."
                )
            else:
                open_call += (
                    " Despite a solid session yesterday, sellers are pushing back in pre-market."
                    " Watch the open closely — early weakness that holds is a sign the"
                    " prior rally may need to consolidate."
                )
        else:
            open_call = (
                f"**Pre-market futures are mixed** ({fut_detail}),"
                " offering no clear directional conviction."
                " The open may be choppy — watch the first 30 minutes for a directional read."
            )
        parts.append(open_call)

    # Overnight APAC
    apac = [i for i in intl_indices if i.get("region") == "Asia-Pacific" and i.get("daily_pct") is not None]
    if apac:
        apac_sorted = sorted(apac, key=lambda x: x["daily_pct"], reverse=True)
        best_apac   = apac_sorted[0]
        worst_apac  = apac_sorted[-1]
        up_count    = sum(1 for i in apac if i["daily_pct"] >= 0)
        down_count  = len(apac) - up_count

        if up_count == len(apac):
            apac_tone = "APAC closed broadly higher overnight"
        elif down_count == len(apac):
            apac_tone = "APAC closed broadly lower overnight"
        else:
            apac_tone = f"APAC was mixed overnight ({up_count} up, {down_count} down)"

        apac_detail = f"{best_apac['name']} led ({best_apac['daily_pct']:+.2f}%)"
        if best_apac["name"] != worst_apac["name"]:
            apac_detail += f", while {worst_apac['name']} lagged ({worst_apac['daily_pct']:+.2f}%)"

        parts.append(f"{apac_tone} — {apac_detail}.")

    # Today's economic events
    high_today = [e for e in (today_events or []) if e.get("importance", 0) >= 3]
    mid_today  = [e for e in (today_events or []) if e.get("importance", 0) >= 2]

    if high_today:
        event_names = [e.get("event", "") for e in high_today]
        names_str   = ", ".join(event_names[:3])
        time_strs   = list({e.get("time_est", e.get("time", "")) for e in high_today if e.get("time_est") or e.get("time")})
        time_str    = f" at {time_strs[0]}" if len(time_strs) == 1 else ""

        names_lower = " ".join(event_names).lower()
        has_cpi  = "cpi"  in names_lower
        has_gdp  = "gdp"  in names_lower
        has_pce  = "pce"  in names_lower
        has_jobs = any(kw in names_lower for kw in ["nfp", "payroll", "claims", "employment"])

        if has_cpi:
            parts.append(
                f"**{names_str} is today's key risk event{time_str}.**"
                f" A hot print pushes yields higher, pressures growth stocks (QQQ), and"
                f" pushes out the Fed's rate-cut timeline — defensives (XLU, XLP) and TIPS"
                f" would benefit. A cool print revives rate-cut hopes and lifts long bonds"
                f" (TLT) and tech. Either way, be positioned before the release, not after."
            )
        elif has_gdp and has_pce:
            gdp_name = next((n for n in event_names if "gdp" in n.lower()), "GDP")
            pce_name = next((n for n in event_names if "pce" in n.lower()), "PCE")
            parts.append(
                f"**{gdp_name} and {pce_name} both print{time_str} — a binary setup.**"
                f" Weak GDP + hot PCE is a stagflation signal and the worst combination"
                f" for equities. Strong GDP + tame PCE keeps the soft-landing story intact."
                f" Position before the print, not after."
            )
        elif has_gdp:
            parts.append(
                f"**{names_str} prints{time_str}.**"
                f" A weak number shifts sentiment toward defensives (XLU, XLP) and bonds;"
                f" a strong beat supports cyclicals (XLY, XLI) and risk-on positioning."
            )
        elif has_jobs:
            parts.append(
                f"**{names_str} prints{time_str}.**"
                f" Strong jobs data complicates the Fed's rate-cut math and could push"
                f" yields higher; a weak print revives easing hopes. Position before the release."
            )
        else:
            verb = "print" if len(event_names) > 1 else "prints"
            parts.append(
                f"**{names_str} {verb}{time_str} today.**"
                f" Watch for a surprise in either direction — these releases can move"
                f" bonds and rate-sensitive sectors quickly."
            )
    elif mid_today:
        names_str = ", ".join(e.get("event", "") for e in mid_today[:2])
        parts.append(
            f"**Today's calendar is light ({names_str}),** so the session will likely"
            f" be driven by news flow and follow-through from overnight momentum"
            f" rather than data surprises. Watch for any geopolitical or Fed commentary"
            f" that could reset the tape."
        )
    else:
        parts.append(
            "**No major US economic releases are scheduled today,** so direction will"
            " come entirely from news flow, geopolitical developments, and any Fed"
            " speakers. Quiet data days can amplify headline-driven moves in either direction."
        )

    return "\n\n".join(parts)


def generate_daybreak_plain_summary(us_indices: list, intl_indices: list,
                                     futures: list, today_events: list,
                                     news_items: list = None,
                                     yesterday_events: list = None,
                                     fx: list = None) -> str:
    """Plain-English 'What This Means' section for the morning brief.

    Produces 4 connected paragraphs:
    1. What happened — full session recap with all major indices + cross-asset
    2. Why it happened — causal narrative linking news/data to price action
    3. What it means for you — portfolio implications and ETF signals
    4. Going into today — pre-market, overnight context, today's catalysts
    """
    if news_items is None:
        news_items = []
    if yesterday_events is None:
        yesterday_events = []

    sp       = next((i for i in us_indices if "S&P"     in i["name"]), None)
    nasdaq   = next((i for i in us_indices if "Nasdaq"  in i["name"]), None)
    dow      = next((i for i in us_indices if "Dow"     in i["name"]), None)
    russell  = next((i for i in us_indices if "Russell" in i["name"]), None)
    gold     = next((i for i in us_indices if i["name"] == "Gold"), None)
    treasury = next((i for i in us_indices if "Treasury" in i["name"]), None)
    usd      = next((i for i in us_indices if i["name"] == "USD Index"), None)
    oil      = next((i for i in us_indices if "WTI" in i["name"] or "Crude" in i["name"]), None)

    themes = _detect_dominant_themes(news_items, yesterday_events)

    lines = []

    # Para 1: What happened
    p1 = _build_what_happened_para(sp, nasdaq, dow, russell, gold, treasury, usd, oil)
    if p1:
        lines.append(p1)

    # Para 2: Why it happened
    p2 = _build_why_it_happened_para(sp, nasdaq, russell, treasury, gold, usd, oil,
                                      news_items, yesterday_events, themes)
    if p2:
        lines.append(p2)

    # Para 3: What it means for you
    p3 = _build_investor_implications_para(sp, nasdaq, russell, treasury, gold, usd, oil,
                                            news_items, yesterday_events, themes)
    if p3:
        lines.append(p3)

    # Para 4: Going into today
    p4 = _build_going_into_today_para(futures, intl_indices, today_events, sp)
    if p4:
        lines.append(p4)

    if not lines:
        return "No strong signals to call out this morning."

    return "\n\n".join(lines)


# ── Positioning Tips ──────────────────────────────────────────────────────────

def generate_daybreak_positioning_tips(us_indices: list, futures: list,
                                        yesterday_events: list,
                                        today_events: list,
                                        news_items: list = None) -> list:
    """Generate specific, data-driven positioning tips for the daily brief."""
    tips = []
    news_items = news_items or []

    sp      = next((i for i in us_indices if "S&P"     in i["name"]), None)
    nasdaq  = next((i for i in us_indices if "Nasdaq"  in i["name"]), None)
    russell = next((i for i in us_indices if "Russell" in i["name"]), None)
    gold    = next((i for i in us_indices if i["name"] == "Gold"), None)
    treasury = next((i for i in us_indices if "Treasury" in i["name"]), None)
    usd     = next((i for i in us_indices if i["name"] == "USD Index"), None)
    oil     = next((i for i in us_indices if "WTI" in i["name"] or "Crude" in i["name"]), None)

    sp_pct    = sp["daily_pct"]              if sp       and sp.get("daily_pct")      is not None else None
    gold_pct  = gold["daily_pct"]            if gold     and gold.get("daily_pct")    is not None else None
    tsy_bps   = treasury.get("yield_change_bps") if treasury else None
    tsy_close = treasury.get("close")        if treasury else None
    oil_close = oil.get("close")             if oil else None
    oil_pct   = oil["daily_pct"]             if oil      and oil.get("daily_pct")     is not None else None

    # Detect dominant themes from headlines
    all_text = " ".join(
        item.get("headline", "") + " " + item.get("summary", "") for item in news_items
    ).lower()
    geo_score   = sum(1 for kw in ["war", "iran", "hormuz", "israel", "ukraine", "military", "missile"] if kw in all_text)
    trade_score = sum(1 for kw in ["tariff", "trade war", "sanction", "embargo"] if kw in all_text)

    # ── Equity futures (S&P, Nasdaq, Dow only — not gold/oil/bonds) ───────────
    fut_with_data  = [f for f in futures if f.get("daily_pct") is not None]
    equity_futures = [f for f in fut_with_data if any(kw in f.get("name", "") for kw in ["S&P", "Nasdaq", "Dow"])]
    if equity_futures:
        all_green = all(f["daily_pct"] >= 0 for f in equity_futures)
        all_red   = all(f["daily_pct"] <  0 for f in equity_futures)
        sp_fut    = next((f for f in equity_futures if "S&P" in f["name"]), None)
        nq_fut    = next((f for f in equity_futures if "Nasdaq" in f["name"]), None)
        val       = f"{sp_fut['daily_pct']:+.2f}%" if sp_fut else "positive"
        if all_green:
            nq_str = f", Nasdaq {nq_fut['daily_pct']:+.2f}%" if nq_fut else ""
            context = (
                " -- market is treating yesterday's pullback as a dip. "
                "Consider holding or adding to broad exposure (SPY, QQQ); "
                "watch for follow-through conviction in the first 30 minutes."
                if sp_pct and sp_pct < 0 else
                " -- risk-on momentum carrying into today. "
                "Broad market (SPY, QQQ) and cyclicals (XLY, XLI) are set up for follow-through."
            )
            tips.append(f"Equity futures are green (S&P {val}{nq_str}){context}")
        elif all_red:
            tips.append(
                f"Equity futures are red (S&P {val})"
                " -- sellers extending yesterday's weakness. "
                "Consider waiting for price to stabilise before adding long exposure; "
                "defensives (XLU, XLP) and short-duration bonds offer relative shelter."
            )

    # ── Geopolitics / oil ─────────────────────────────────────────────────────
    if geo_score >= 2:
        if oil_close is not None and oil_close > 95:
            tips.append(
                f"Geopolitical risk remains elevated with oil at ${oil_close:,.2f}/bbl"
                " -- Energy ETFs (XLE) benefit from sustained high oil, but are also first to "
                "reverse on de-escalation headlines. Consider sizing energy exposure with "
                "a tight stop rather than adding outright."
            )
        else:
            tips.append(
                "Geopolitical headlines remain the dominant risk factor today"
                " -- keep exposure to energy (XLE), defence (ITA), and safe-haven assets "
                "(GLD, TLT) in focus. These are the fastest-moving sectors when "
                "escalation/de-escalation news breaks."
            )

    # ── Gold counter-intuitive move ───────────────────────────────────────────
    if gold_pct is not None and gold_pct < -0.5 and sp_pct is not None and sp_pct < 0:
        tips.append(
            f"Gold fell {abs(gold_pct):.2f}% alongside stocks — safe-haven bid went to the dollar"
            " -- if you hold GLD as a hedge, it didn't play its role yesterday. "
            "Consider whether short-term USD exposure (UUP) better reflects current market stress."
        )
    elif gold_pct is not None and gold_pct > 0.5 and sp_pct is not None and sp_pct < 0:
        tips.append(
            f"Gold rose {gold_pct:.2f}% while stocks declined — classic risk-off rotation"
            " -- GLD is actively hedging portfolio drawdown. "
            "Consider maintaining or modestly adding to the position."
        )

    # ── Treasury yield ────────────────────────────────────────────────────────
    if tsy_bps is not None and tsy_close is not None and abs(tsy_bps) >= 4:
        if tsy_bps > 0:
            tips.append(
                f"10-year yield rose {round(abs(tsy_bps))} bps to {tsy_close:.2f}% -- "
                "higher yields compress growth-stock valuations most. "
                "Tilt away from long-duration tech (QQQ) toward value (VTV) and "
                "dividend payers (SCHD, DVY) until yields stabilise."
            )
        else:
            tips.append(
                f"10-year yield fell {round(abs(tsy_bps))} bps to {tsy_close:.2f}% -- "
                "falling yields support long-duration assets: growth stocks (QQQ), "
                "REITs (VNQ), and long bonds (TLT) all benefit. "
                "Consider adding duration if the yield trend holds."
            )

    # ── USD direction ─────────────────────────────────────────────────────────
    if usd and usd.get("daily_pct") is not None and abs(usd["daily_pct"]) >= 0.5:
        if usd["daily_pct"] > 0:
            tips.append(
                f"Dollar strengthened {usd['daily_pct']:+.2f}% -- headwind for "
                "multinationals (many S&P 500 earners), EM stocks (EEM, VWO), "
                "and commodities (GLD, DJP). Consider trimming international "
                "and commodity exposure proportionally."
            )
        else:
            tips.append(
                f"Dollar weakened {usd['daily_pct']:+.2f}% -- tailwind for "
                "international equities and commodities. "
                "EM funds (EEM, VWO) and commodity ETFs (GLD, DJP) "
                "benefit from dollar softness; consider tilting toward these."
            )

    # ── Oil price level ───────────────────────────────────────────────────────
    if oil_close is not None and oil_close > 100 and geo_score < 2:
        tips.append(
            f"WTI crude at ${oil_close:,.2f}/bbl -- above $100 starts to bite "
            "consumer spending and keeps inflation sticky. "
            "Watch transport (XTN) and consumer discretionary (XLY) for margin pressure; "
            "energy (XLE) benefits but the macro drag is a risk offset."
        )

    # ── Yesterday's data surprises ────────────────────────────────────────────
    for event in (yesterday_events or []):
        name     = event.get("event", "").lower()
        surprise = event.get("surprise", "")
        actual   = event.get("actual", "--")
        expected = event.get("expected", "--")
        unit     = event.get("unit", "")
        if "cpi" in name and "core" not in name and surprise == "above":
            tips.append(
                f"CPI came in hot ({actual}{unit} vs. {expected}{unit} expected) -- "
                "inflation staying elevated limits the Fed's room to cut. "
                "TIPS (TIP), defensives (XLU, XLP), and short-duration bonds "
                "hold up better in persistent-inflation regimes."
            )
        if "retail sales" in name and surprise == "above":
            tips.append(
                f"Retail sales beat ({actual}{unit} vs. {expected}{unit}) -- "
                "consumer remains resilient. Consumer discretionary (XLY) "
                "and cyclicals (XLI) may see follow-through buying."
            )
        if "jobless claims" in name and surprise == "below":
            tips.append(
                "Jobless claims below expectations -- labor market staying tight. "
                "Risk-on positioning is supported; the Fed is less likely to cut "
                "aggressively, which keeps pressure on rate-sensitive sectors (XLU, XLRE)."
            )

    # ── Today's catalysts ─────────────────────────────────────────────────────
    for event in (today_events or []):
        name = event.get("event", "").lower()
        imp  = event.get("importance", 0)
        if imp < 3:
            continue
        if "fomc" in name:
            tips.append(
                "FOMC announcement today -- high volatility expected around the decision. "
                "Consider trimming position sizes before the announcement; "
                "re-enter after the initial reaction settles (typically 15-30 min post-release)."
            )
        elif "pce" in name:
            tips.append(
                "PCE (Fed's preferred inflation gauge) prints today. "
                "Hot print: reduce TLT, add TIPS and defensives. "
                "Cool print: add QQQ and growth; TLT benefits from rate-cut repricing."
            )
        elif "gdp" in name:
            tips.append(
                "GDP prints today. Weak number: rotate to defensives (XLU, XLP) and bonds. "
                "Strong beat: cyclicals (XLY, XLI) and financials (XLF) are set up well."
            )
        elif "cpi" in name:
            tips.append(
                "CPI prints today. Hot: TIPS, defensives, trim growth. "
                "Cool: add QQQ and TLT -- rate-cut hopes revive quickly on a downside surprise."
            )

    # ── Fallback: specific to today's conditions ──────────────────────────────
    if not tips:
        if sp_pct is not None and sp_pct < -0.5:
            tips.append(
                f"S&P 500 pulled back {abs(sp_pct):.2f}% yesterday with no major catalyst -- "
                "routine pullbacks in uptrends are typically buying opportunities. "
                "Hold current allocations; watch today's open for directional confirmation."
            )
        elif sp_pct is not None and sp_pct > 0.5:
            tips.append(
                f"S&P 500 gained {sp_pct:.2f}% yesterday -- no immediate action needed. "
                "Monitor for any signs of overextension if today's open gaps up further."
            )
        else:
            tips.append(
                "No high-conviction signals today -- maintain current allocations. "
                "Focus on position sizing rather than direction; "
                "a light data calendar means headline risk drives intraday moves."
            )

    return tips[:6]


# ── LinkedIn Post Generator ───────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Remove Markdown formatting for plain-text platforms like LinkedIn."""
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **bold** → bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)         # *italic* → italic
    text = re.sub(r'^- ', '', text, flags=re.MULTILINE)  # list items
    return text


def generate_linkedin_post(context: dict) -> str:
    """Generate a LinkedIn-ready plain-text post from the daybreak context.

    Format:
        Hook sentence (first paragraph of plain_summary, bold stripped)

        Body (remaining plain_summary paragraphs, markdown stripped)

        Best: {label} ({pct}%) | Worst: {label} ({pct}%)

        Positioning: {first tip, markdown stripped}

        Full breakdown → frameworkfoundry.info

        #MacroInvesting #ETFs #MarketOpen
    """
    plain_summary = context.get("plain_summary", "")
    paragraphs = [p.strip() for p in plain_summary.split("\n\n") if p.strip()]

    if paragraphs:
        hook = _strip_markdown(paragraphs[0])
        body_parts = [_strip_markdown(p) for p in paragraphs[1:]]
        body = "\n\n".join(body_parts)
    else:
        hook = ""
        body = ""

    # Best / worst line
    us_best  = context.get("us_best")
    us_worst = context.get("us_worst")
    if us_best and us_worst:
        best_line = (
            f"Best: {us_best['name']} ({us_best['daily_pct']:+.2f}%)"
            f" | Worst: {us_worst['name']} ({us_worst['daily_pct']:+.2f}%)"
        )
    else:
        best_line = ""

    # First positioning tip
    tips = context.get("tips") or context.get("positioning_tips") or []
    positioning = _strip_markdown(tips[0]) if tips else ""

    # Assemble post
    title = _generate_post_title(context)
    parts = []
    if title:
        parts.append(title)
    if hook:
        parts.append(hook)
    if body:
        parts.append(body)
    if best_line:
        parts.append(best_line)
    if positioning:
        parts.append(f"Positioning: {positioning}")
    parts.append("Full breakdown → frameworkfoundry.info")
    parts.append("#MacroInvesting #ETFs #MarketOpen")

    post = "\n\n".join(parts)

    # LinkedIn personal post limit is 3,000 characters
    LINKEDIN_LIMIT = 3000
    if len(post) > LINKEDIN_LIMIT:
        overage = len(post) - LINKEDIN_LIMIT
        import warnings
        warnings.warn(
            f"LinkedIn post is {len(post)} chars — {overage} over the 3,000-char limit. "
            "Trim the plain_summary or positioning tip before posting.",
            UserWarning,
            stacklevel=2,
        )

    return post


def generate_x_post(context: dict) -> str:
    """Generate a 3-tweet thread for X (Twitter) from the daybreak context.

    Returns three blocks separated by '\\n---\\n', each ≤280 chars.
    Warns via UserWarning if any block exceeds the limit.
    """
    import warnings

    plain_summary = context.get("plain_summary", "")
    paragraphs = [p.strip() for p in plain_summary.split("\n\n") if p.strip()]
    first_sentence = ""
    if paragraphs:
        raw = _strip_markdown(paragraphs[0])
        # Take just the first sentence
        end = raw.find(". ")
        first_sentence = raw[: end + 1].strip() if end != -1 else raw.strip()

    us_best  = context.get("us_best")
    us_worst = context.get("us_worst")
    if us_best and us_worst:
        best_line = (
            f"Best: {us_best['name']} {us_best['daily_pct']:+.2f}%"
            f" | Worst: {us_worst['name']} {us_worst['daily_pct']:+.2f}%"
        )
    else:
        best_line = ""

    today_events = context.get("today_events") or []
    if today_events:
        event_names = ", ".join(e.get("event", e.get("name", "")) for e in today_events)
        calendar_line = f"Today's calendar: {event_names}"
    else:
        calendar_line = "Quiet day — no major releases"

    tips = context.get("tips") or context.get("positioning_tips") or []
    first_tip = _strip_markdown(tips[0]) if tips else ""

    title = _generate_post_title(context)
    tweet1_parts = [p for p in [title or first_sentence, best_line, "🧵 1/3"] if p]
    tweet1 = "\n\n".join(tweet1_parts)

    tweet2_parts = [p for p in [calendar_line, first_tip, "🧵 2/3"] if p]
    tweet2 = "\n\n".join(tweet2_parts)

    tweet3 = "Full daily brief → frameworkfoundry.info\n\n#MacroInvesting #ETFs #MarketOpen\n\n🧵 3/3"

    TWEET_LIMIT = 280
    for i, tweet in enumerate([tweet1, tweet2, tweet3], start=1):
        if len(tweet) > TWEET_LIMIT:
            overage = len(tweet) - TWEET_LIMIT
            warnings.warn(
                f"X thread tweet {i}/3 is {len(tweet)} chars — {overage} over the 280-char limit. "
                "Trim before posting.",
                UserWarning,
                stacklevel=2,
            )

    return f"{tweet1}\n---\n{tweet2}\n---\n{tweet3}"


def _generate_post_title(context: dict) -> str:
    """Generate the most newsworthy title from the day's data.

    Priority:
    1. Extreme mover (>3% in any single asset) — leads the headline.
       If a high-importance event also printed yesterday, append it.
    2. High-importance yesterday event with a confirmed actual value.
    3. Fallback: market direction + today's calendar.
    """
    us_indices       = context.get("us_indices") or []
    yesterday_events = context.get("yesterday_events") or []
    today_events     = context.get("today_events") or []

    _SHORT_NAMES = {
        "WTI Crude Oil": "Oil", "Gold": "Gold", "S&P 500": "S&P 500",
        "Nasdaq": "Nasdaq", "Dow Jones": "Dow", "Russell 2000": "Small Caps",
        "10Y Treasury": "Treasuries", "USD Index": "Dollar",
    }

    def _spx_direction(indices):
        sp = next((i for i in indices if "S&P" in i.get("name", "")), None)
        pct = sp["daily_pct"] if sp and sp.get("daily_pct") is not None else 0
        if pct >= 1.0:   return "rallied"
        if pct >= 0.2:   return "edged higher"
        if pct > -0.2:   return "held flat"
        if pct > -1.0:   return "pulled back"
        return "sold off"

    def _event_actual_short(event):
        """Return just the MoM figure if the actual is a combined MoM/YoY string."""
        actual = event.get("actual", "--")
        if actual == "--":
            return None
        return actual.split(" MoM")[0] if " MoM" in actual else actual

    # 1. Extreme mover
    big_movers = [
        (i["name"], i["daily_pct"])
        for i in us_indices
        if i.get("daily_pct") is not None and abs(i["daily_pct"]) >= 3.0
    ]
    if big_movers:
        big_movers.sort(key=lambda x: abs(x[1]), reverse=True)
        name, pct = big_movers[0]
        short = _SHORT_NAMES.get(name, name)
        verb  = "Surges" if pct > 0 else "Tumbles"
        mover = f"{short} {verb} {abs(pct):.0f}%"

        high = [e for e in yesterday_events
                if e.get("importance", 0) >= 3 and _event_actual_short(e)]
        if high:
            ev_name = high[0].get("event", "")
            actual  = _event_actual_short(high[0])
            return f"{mover} — {ev_name} Prints {actual}"
        return f"{mover} — What It Means at the Open"

    # 2. Key event printed yesterday
    high = [e for e in yesterday_events
            if e.get("importance", 0) >= 3 and _event_actual_short(e)]
    if high:
        ev_name  = high[0].get("event", "")
        actual   = _event_actual_short(high[0])
        surprise = high[0].get("surprise", "neutral").lower()
        direction = _spx_direction(us_indices)
        if surprise == "above":
            return f"{ev_name} Comes in Hot at {actual} — Markets {direction.title()}"
        if surprise == "below":
            return f"{ev_name} Misses at {actual} — Markets {direction.title()}"
        return f"{ev_name} Prints {actual} — Markets {direction.title()}"

    # 3. Fallback: direction + today's calendar
    top_event = (today_events[0].get("event", today_events[0].get("name", ""))
                 if today_events else "")
    sp = next((i for i in us_indices if "S&P" in i.get("name", "")), None)
    pct = sp["daily_pct"] if sp and sp.get("daily_pct") is not None else None
    if pct is not None:
        if pct >= 1.0:   d = "rally"
        elif pct >= 0.2: d = "gains"
        elif pct > -0.2: d = "flat"
        elif pct > -1.0: d = "dip"
        else:            d = "selloff"
    else:
        d = "mixed session"

    if top_event:
        return {
            "rally":        f"{top_event} Ahead — Markets Rallied. Stay Positioned.",
            "gains":        f"{top_event} Day: Stocks Nudged Higher. Here's the Playbook.",
            "flat":         f"{top_event} Prints Today — Markets Treading Water.",
            "dip":          f"{top_event} Day: Stocks Dipped. Here's Where to Stand.",
            "selloff":      f"{top_event} Looms After Yesterday's Selloff.",
            "mixed session": f"{top_event} on the Calendar — Markets Sent Mixed Signals.",
        }.get(d, f"{top_event}: What to Watch Before the Open")

    return {
        "rally":        "Markets Rallied — Here's What It Means for Your ETFs",
        "gains":        "Quiet Gains Yesterday — What to Watch Today",
        "flat":         "Flat Open Ahead — No Major Catalysts, But Stay Sharp",
        "dip":          "Stocks Slipped — Dip or Warning Sign?",
        "selloff":      "After the Selloff: Where to Position Now",
        "mixed session": "Mixed Signals — How to Read Today's Open",
    }.get(d, "Market Day Break — Daily Brief")


def _md_to_html(text: str) -> str:
    """Convert a block of Markdown text to HTML paragraphs.

    Handles: **bold**, *italic*, [text](url), bare paragraphs, bullet lists,
    numbered lists, and --- dividers.
    """
    import re

    def inline(t: str) -> str:
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
        t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
        return t

    lines = text.split("\n")
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if re.match(r'^---+$', line.strip()):
            html_parts.append("<hr>")
        elif re.match(r'^## ', line):
            html_parts.append(f"<h2>{inline(line[3:].strip())}</h2>")
        elif re.match(r'^# ', line):
            html_parts.append(f"<h1>{inline(line[2:].strip())}</h1>")
        elif re.match(r'^- ', line):
            # Collect consecutive bullet items
            items = []
            while i < len(lines) and re.match(r'^- ', lines[i]):
                items.append(f"<li>{inline(lines[i][2:].strip())}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif re.match(r'^\d+\. ', line):
            # Collect consecutive numbered items
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                items.append(f"<li>{inline(re.sub(r'^\d+\. ', '', lines[i]))}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        elif line.strip():
            html_parts.append(f"<p>{inline(line.strip())}</p>")

        i += 1

    return "\n".join(html_parts)


def generate_substack_post(context: dict) -> str:
    """Generate an HTML draft for pasting into Substack's editor."""
    from datetime import datetime

    date_str = context.get("date", "")
    try:
        date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %-d, %Y")
    except (ValueError, TypeError):
        date_display = date_str

    title = _generate_post_title(context)
    narrative = context.get("narrative", "")
    plain_summary = context.get("plain_summary", "")

    today_events = context.get("today_events") or []
    if today_events:
        events_lines = "\n".join(
            f"- **{e.get('event', e.get('name', ''))}**"
            + (f" — {e.get('time', '')}" if e.get("time") else "")
            for e in today_events
        )
    else:
        events_lines = "_No major economic releases scheduled today._"

    tips = context.get("tips") or context.get("positioning_tips") or []
    tips_lines = "\n".join(f"{n}. {tip}" for n, tip in enumerate(tips, start=1)) if tips else "_No positioning notes for today._"

    subtitle = f"Daily macro intelligence for ETF investors · {date_display}"

    body_md = "\n\n".join([
        narrative,
        "---",
        f"## What This Means for Your Portfolio\n\n{plain_summary}",
        "---",
        f"## Today's Watch List\n\n{events_lines}",
        "---",
        f"## Positioning Notes\n\n{tips_lines}",
        "---",
        "*Full data tables and overnight markets: [frameworkfoundry.info](https://frameworkfoundry.info)*\n\n*Framework Capital Weekly · Unsubscribe*",
    ])

    return (
        f"<h1>{title}</h1>\n"
        f"<h3>{subtitle}</h3>\n"
        f"<hr>\n"
        f"{_md_to_html(body_md)}\n"
    )


# ── Context builder ───────────────────────────────────────────────────────────

def build_daybreak_context(raw: dict) -> dict:
    """Build the full template context for the daybreak edition.

    Args:
        raw: Full daybreak payload from fetch_daybreak_data().

    Returns:
        Dict ready for Jinja2 rendering and HTML generation.
    """
    date_str = raw.get("meta", {}).get("date", "")

    us_indices   = process_us_close(raw.get("us_close", {}))
    intl_indices = process_intl_overnight(raw.get("intl_overnight", {}))
    fx_rates     = process_fx(raw.get("fx", {}))
    futures      = process_futures(raw.get("futures", {}))

    yesterday_events = raw.get("econ_calendar", {}).get("yesterday", [])
    today_events     = raw.get("econ_calendar", {}).get("today", [])

    market_news_raw = raw.get("market_news", [])

    narrative    = generate_daybreak_narrative(us_indices, intl_indices,
                                               fx_rates, futures)
    plain_summary = generate_daybreak_plain_summary(
        us_indices, intl_indices, futures, today_events,
        news_items=market_news_raw,
        yesterday_events=yesterday_events,
        fx=fx_rates,
    )
    tips         = generate_daybreak_positioning_tips(us_indices, futures,
                                                       yesterday_events, today_events,
                                                       news_items=market_news_raw)

    # ── Editorial overrides (stored in fixture under "editorial" key) ──────────
    editorial = raw.get("editorial", {})
    if editorial.get("narrative_suffix"):
        narrative = narrative.rstrip() + " " + editorial["narrative_suffix"]
    if editorial.get("plain_summary"):
        plain_summary = editorial["plain_summary"]
    for extra_tip in editorial.get("extra_tips", []):
        tips.append(extra_tip)

    # Best / worst — exclude yields (daily_pct is yield %, not bond price %) and non-table entries
    all_us = [i for i in us_indices if i["daily_pct"] is not None
              and i.get("table", True) and not i.get("is_yield", False)]
    all_us_sorted = sorted(all_us, key=lambda x: x["daily_pct"], reverse=True)
    us_best  = all_us_sorted[0]  if all_us_sorted else None
    us_worst = all_us_sorted[-1] if all_us_sorted else None

    return {
        "date":           date_str,
        "edition":        "Daily Edition",
        "tagline":        "Daily Edition \u00b7 Market intelligence at the open",
        "region_banner":  "Coverage: US Close \u00b7 Asia-Pacific \u00b7 Europe \u00b7 FX \u00b7 Macro",
        "narrative":      narrative,
        "plain_summary":  plain_summary,
        "market_news":    process_market_news(market_news_raw),
        "us_indices":     us_indices,
        "intl_indices":   intl_indices,
        "fx_rates":       fx_rates,
        "futures":        futures,
        "yesterday_events": yesterday_events,
        "today_events":     today_events,
        "tips":           tips,
        "us_best":        us_best,
        "us_worst":       us_worst,
    }
