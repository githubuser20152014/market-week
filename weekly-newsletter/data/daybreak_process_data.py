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
        para1 = f"At market close, {tone} — the S&P 500 ended {pct:+.2f}%"
        if nasdaq and nasdaq["daily_pct"] is not None:
            para1 += f", while the Nasdaq finished {nasdaq['daily_pct']:+.2f}%"
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


def _build_cross_indicator_para(us_indices: list, news_items: list,
                                 yesterday_events: list) -> str:
    """Return a paragraph connecting the dominant theme to yield/equity/gold signals."""
    sp       = next((i for i in us_indices if "S&P" in i["name"]), None)
    nasdaq   = next((i for i in us_indices if "Nasdaq" in i["name"]), None)
    russell  = next((i for i in us_indices if "Russell" in i["name"]), None)
    treasury = next((i for i in us_indices if "Treasury" in i["name"]), None)
    gold     = next((i for i in us_indices if i["name"] == "Gold"), None)

    sp_pct    = sp["daily_pct"]              if sp      and sp.get("daily_pct")      is not None else None
    tsy_bps   = treasury.get("yield_change_bps") if treasury else None
    tsy_close = treasury.get("close")        if treasury else None
    gold_pct  = gold["daily_pct"]            if gold    and gold.get("daily_pct")    is not None else None

    themes          = _detect_dominant_themes(news_items or [], yesterday_events or [])
    fed_prominent   = themes.get("fed", 0) > 0
    trade_prominent = themes.get("trade", 0) > 0
    geo_prominent   = themes.get("geopolitics", 0) > 0

    parts = []

    # ── Yield + equity connection ──────────────────────────────────────────────
    if tsy_bps is not None and abs(tsy_bps) >= 4 and tsy_close is not None:
        bps = round(abs(tsy_bps))
        if tsy_bps > 0 and sp_pct is not None and sp_pct < 0:
            if fed_prominent:
                lead = (
                    f"**Markets are repricing the Fed.** Bond yields climbed {bps} bps "
                    f"to {tsy_close:.2f}% as headlines confirmed what the bond market has "
                    f"been telegraphing: hopes for rate cuts are rapidly fading. "
                    f"Higher yields at current levels make it harder to justify equity "
                    f"valuations, particularly in growth and small caps"
                )
                if nasdaq and nasdaq.get("daily_pct") and russell and russell.get("daily_pct"):
                    lead += (
                        f" — which explains why the Nasdaq ({nasdaq['daily_pct']:+.2f}%) "
                        f"and Russell ({russell['daily_pct']:+.2f}%) led the decline."
                    )
                else:
                    lead += "."
                parts.append(lead)
            else:
                parts.append(
                    f"**Bond yields climbed {bps} bps to {tsy_close:.2f}%**, making it "
                    f"harder to justify equity valuations — particularly in growth and small caps."
                )
        elif tsy_bps < 0 and sp_pct is not None and sp_pct < 0:
            parts.append(
                f"**Bond yields fell {bps} bps to {tsy_close:.2f}%** — a flight-to-safety "
                f"signal that reinforces the risk-off read."
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

    # ── Trade / geopolitics paragraph ─────────────────────────────────────────
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
            risk_para = f"**Trade risk added fuel.** {trade_headline}."
            if geo_context:
                risk_para += (
                    f" Combined with ongoing {geo_context}, investors are pricing in "
                    f"more geopolitical premium."
                )
            parts.append(risk_para)
        elif geo_prominent and geo_context:
            parts.append(
                f"**Geopolitical risk remains elevated.** {geo_context.capitalize()} "
                f"continued to weigh on sentiment."
            )

    # ── Gold: fold counter-intuitive move into last paragraph ─────────────────
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
                f"Gold climbed {gold_pct:.2f}% alongside the equity selloff — "
                f"investors are rotating into safe havens, amplifying the risk-off signal."
            )

    return "\n\n".join(parts)


def _build_binary_event_para(high_today: list, fut_with_data: list) -> str:
    """Frame today's key events as a binary outcome with a futures-lean signal."""
    event_names       = [e.get("event", "") for e in high_today]
    event_names_lower = [n.lower() for n in event_names]

    has_gdp = any("gdp" in n for n in event_names_lower)
    has_pce = any("pce" in n for n in event_names_lower)
    has_cpi = any("cpi" in n for n in event_names_lower)

    # Build futures lean string
    fut_lean = ""
    if fut_with_data:
        equity_futs = [f for f in fut_with_data if any(
            kw in f.get("name", "") for kw in ["S&P", "Nasdaq", "Dow"]
        )]
        all_green = equity_futs and all(f["daily_pct"] >= 0 for f in equity_futs)
        all_red   = equity_futs and all(f["daily_pct"] < 0  for f in equity_futs)
        sp_fut    = next((f for f in fut_with_data if "S&P" in f.get("name", "")), None)
        pct_str   = f" ({sp_fut['daily_pct']:+.2f}%)" if sp_fut else ""
        if all_green:
            fut_lean = f"mildly green futures{pct_str} suggest the market is leaning that way, but isn't committing"
        elif all_red:
            fut_lean = f"mildly red futures{pct_str} suggest caution heading into the print"

    # Shared time string
    times = list({
        e.get("time_est", e.get("time", ""))
        for e in high_today
        if e.get("time_est") or e.get("time")
    })
    time_str = f" at {times[0]}" if len(times) == 1 else ""

    if has_gdp and has_pce:
        gdp_name = next((n for n in event_names if "gdp" in n.lower()), "GDP")
        pce_name = next((n for n in event_names if "pce" in n.lower()), "PCE")
        para = (
            f"**This morning is binary.** {gdp_name} and {pce_name} both print{time_str}. "
            f"A weak {gdp_name} + hot {pce_name} would be a stagflation signal, likely "
            f"extending yesterday's losses. A strong {gdp_name} + tame {pce_name} keeps "
            f"the soft-landing narrative intact"
        )
        if fut_lean:
            para += f" — {fut_lean}"
        para += ". Position before the print, not after."
        return para

    if has_gdp:
        gdp_name = next((n for n in event_names if "gdp" in n.lower()), "GDP")
        para = (
            f"**Watch the {gdp_name} print{time_str}.** A weak number shifts sentiment "
            f"toward defensives (XLU, XLP); a strong beat supports risk-on positioning "
            f"in cyclicals (XLY, XLI)"
        )
        if fut_lean:
            para += f" — {fut_lean}"
        para += ". Position before the release."
        return para

    if has_cpi:
        cpi_name = next((n for n in event_names if "cpi" in n.lower()), "CPI")
        para = (
            f"**{cpi_name} prints{time_str} — watch for a surprise in either direction.** "
            f"A hot print pressures growth stocks and pushes yields higher (TIPS, defensives). "
            f"A cool print revives rate-cut hopes and lifts long bonds and tech"
        )
        if fut_lean:
            para += f" — {fut_lean}"
        para += ". Position before the print."
        return para

    # Generic high-importance events
    names_str = " and ".join(event_names[:2])
    verb      = "print" if len(event_names) > 1 else "prints"
    para = (
        f"**{names_str} {verb}{time_str} today** — "
        f"{'these' if len(event_names) > 1 else 'this'} can move markets, particularly "
        f"bonds and rate-sensitive sectors. Be positioned before the release, not after."
    )
    return para


def generate_daybreak_plain_summary(us_indices: list, intl_indices: list,
                                     futures: list, today_events: list,
                                     news_items: list = None,
                                     yesterday_events: list = None) -> str:
    """Plain-English 'What This Means' section for the morning brief.

    Produces 3–4 connected paragraphs:
    1. Breadth analysis (broad vs. narrow, dollar impact)
    2. Dominant theme + cross-indicator narrative (yields, gold, USD linked)
    3. Binary outcome framing for today's key events
    """
    if news_items is None:
        news_items = []
    if yesterday_events is None:
        yesterday_events = []

    lines = []

    sp      = next((i for i in us_indices if "S&P" in i["name"]), None)
    nasdaq  = next((i for i in us_indices if "Nasdaq" in i["name"]), None)
    dow     = next((i for i in us_indices if "Dow" in i["name"]), None)
    russell = next((i for i in us_indices if "Russell" in i["name"]), None)

    # ── Para 1: Breadth analysis ───────────────────────────────────────────────
    if sp and sp["daily_pct"] is not None:
        pct         = sp["daily_pct"]
        dollar_move = abs(pct) * 100  # per $10,000 portfolio

        companions = [i for i in [nasdaq, dow, russell]
                      if i and i.get("daily_pct") is not None]
        all_down = pct < 0 and all(c["daily_pct"] < 0 for c in companions)
        all_up   = pct > 0 and all(c["daily_pct"] > 0 for c in companions)

        if pct < -1.0 and all_down and companions:
            # Broad selloff — list each companion with its pct
            comp_strs = []
            for idx in [russell, nasdaq, dow]:
                if idx and idx.get("daily_pct") is not None:
                    label = {
                        "Russell 2000": "small caps (Russell 2000",
                        "Nasdaq":       "tech (Nasdaq",
                        "Dow Jones":    "blue chips (Dow",
                    }.get(idx["name"], idx["name"])
                    comp_strs.append(f"{label} {idx['daily_pct']:+.2f}%)")
            if comp_strs:
                lines.append(
                    f"**Yesterday's selloff was broad and deep.** The S&P 500 dropped "
                    f"{abs(pct):.1f}%, but the story is in the width: "
                    f"{', '.join(comp_strs)} all fell together — this wasn't sector "
                    f"rotation, it was risk-off across the board. A $10,000 index "
                    f"portfolio lost roughly ${dollar_move:,.0f}."
                )
            else:
                lines.append(
                    f"**Yesterday was a rough session.** The S&P 500 dropped {abs(pct):.1f}%, "
                    f"meaning a $10,000 index portfolio lost about ${dollar_move:,.0f}."
                )

        elif pct < 0 and companions:
            down_comps = [c for c in companions if c["daily_pct"] < 0]
            up_comps   = [c for c in companions if c["daily_pct"] > 0]
            if up_comps and down_comps:
                lines.append(
                    f"**Yesterday's decline was narrow, not broad.** The S&P 500 slipped "
                    f"{abs(pct):.1f}%, but markets weren't in full retreat — some sectors "
                    f"held up. This looks more like rotation than a broad risk-off move."
                )
            else:
                lines.append(
                    f"**Stocks pulled back modestly yesterday.** The S&P 500 lost {abs(pct):.1f}% "
                    f"— a ${dollar_move:,.0f} hit on a $10,000 portfolio, nothing dramatic."
                )

        elif pct > 1.0 and all_up and companions:
            comp_strs = []
            for idx in [nasdaq, dow]:
                if idx and idx.get("daily_pct") is not None:
                    comp_strs.append(f"{idx['name']} {idx['daily_pct']:+.2f}%")
            advance = f" with {' and '.join(comp_strs)} joining the advance" if comp_strs else ""
            lines.append(
                f"**Yesterday's rally was broad-based.** The S&P 500 gained {pct:.1f}%"
                f"{advance} — a clean risk-on session. A $10,000 portfolio added "
                f"roughly ${dollar_move:,.0f}."
            )

        elif pct > 0:
            lines.append(
                f"**Stocks edged higher yesterday.** The S&P 500 was up {pct:+.1f}% "
                f"— a quiet positive session, nothing dramatic."
            )
        else:
            lines.append(
                f"**Stocks slipped modestly yesterday.** The S&P 500 lost {abs(pct):.1f}% "
                f"— a routine dip, not a panic."
            )

    # ── Para 2: Theme + cross-indicator (yields, gold, trade, geopolitics) ─────
    cross_para = _build_cross_indicator_para(us_indices, news_items, yesterday_events)
    if cross_para:
        lines.append(cross_para)

    # ── Para 3: Binary event framing ───────────────────────────────────────────
    fut_with_data = [f for f in futures if f["daily_pct"] is not None]
    high_today    = [e for e in today_events if e.get("importance", 0) >= 3]

    if high_today:
        binary = _build_binary_event_para(high_today, fut_with_data)
        if binary:
            lines.append(binary)
    elif fut_with_data:
        # Fallback futures signal when no high-importance events today
        equity_futs = [f for f in fut_with_data if any(
            kw in f.get("name", "") for kw in ["S&P", "Nasdaq", "Dow"]
        )]
        all_green = equity_futs and all(f["daily_pct"] >= 0 for f in equity_futs)
        all_red   = equity_futs and all(f["daily_pct"] < 0  for f in equity_futs)
        if all_green:
            lines.append(
                "**Pre-market futures are green** — the market is leaning toward a "
                "risk-on open. Watch for follow-through once cash markets open."
            )
        elif all_red:
            lines.append(
                "**Pre-market futures are red** — the market is signalling caution. "
                "Watch whether sellers extend yesterday's weakness or buyers step in."
            )

    if not lines:
        return "No strong signals to call out this morning."

    return "\n\n".join(lines)


# ── Positioning Tips ──────────────────────────────────────────────────────────

def generate_daybreak_positioning_tips(us_indices: list, futures: list,
                                        yesterday_events: list,
                                        today_events: list) -> list:
    """Generate 4-6 rule-based positioning tips for the daily brief.

    Rules mirror process_data.py's generate_positioning_tips() and add
    a futures-direction rule:
    - All futures green → risk-on open signal
    - All futures red   → cautious open signal
    """
    tips = []

    # ── Futures direction ─────────────────────────────────────────────────────
    fut_with_data = [f for f in futures if f["daily_pct"] is not None]
    if fut_with_data:
        all_green = all(f["daily_pct"] >= 0 for f in fut_with_data)
        all_red   = all(f["daily_pct"] < 0  for f in fut_with_data)
        if all_green:
            sp_fut = next((f for f in fut_with_data if "S&P" in f["name"]), None)
            val = f"{sp_fut['daily_pct']:+.2f}%" if sp_fut else "positive"
            tips.append(
                f"All three futures contracts are green (S&P Futures {val})"
                " -- risk-on open signalled. Consider maintaining or adding to "
                "broad market exposure (SPY, QQQ) early in the session."
            )
        elif all_red:
            sp_fut = next((f for f in fut_with_data if "S&P" in f["name"]), None)
            val = f"{sp_fut['daily_pct']:+.2f}%" if sp_fut else "negative"
            tips.append(
                f"All three futures contracts are red (S&P Futures {val})"
                " -- cautious open expected. Consider reducing intraday risk or "
                "waiting for price to stabilise before adding long exposure."
            )

    # ── USD direction ─────────────────────────────────────────────────────────
    usd = next((i for i in us_indices if i["name"] == "USD Index"), None)
    if usd and usd["daily_pct"] is not None and abs(usd["daily_pct"]) >= 0.5:
        if usd["daily_pct"] > 0:
            tips.append(
                f"USD Index strengthened {usd['daily_pct']:+.2f}% yesterday"
                " -- a stronger dollar weighs on multinational earnings and commodities. "
                "Consider trimming exposure to export-heavy sectors and commodity ETFs (GLD, DJP)."
            )
        else:
            tips.append(
                f"USD Index weakened {usd['daily_pct']:+.2f}% yesterday"
                " -- a softer dollar is a tailwind for emerging markets (EEM, VWO) "
                "and commodities (GLD, DJP). Consider tilting toward international "
                "and commodity exposure."
            )

    # ── Yesterday's event-based tips ─────────────────────────────────────────
    for event in yesterday_events:
        name     = event.get("event", "").lower()
        surprise = event.get("surprise", "")
        actual   = event.get("actual", "--")
        expected = event.get("expected", "--")
        unit     = event.get("unit", "")

        if "cpi" in name and "core" not in name and surprise == "above":
            tips.append(
                f"CPI came in hot at {actual}{unit} vs. {expected}{unit} expected yesterday"
                " -- inflation-sensitive sectors may see continued pressure. "
                "Consider TIPS (TIP) or defensive tilts (XLU, XLP)."
            )
        if "retail sales" in name and surprise == "above":
            tips.append(
                f"Retail sales surprised to the upside ({actual}{unit} vs. {expected}{unit})"
                " -- consumer discretionary (XLY) and cyclicals may extend gains."
            )
        if "jobless claims" in name and surprise == "below":
            tips.append(
                "Jobless claims came in lower than expected"
                " -- labor market remains tight, supporting risk-on positioning."
            )

    # ── Today's event-based tips ──────────────────────────────────────────────
    for event in today_events:
        name = event.get("event", "").lower()
        if "fomc" in name:
            tips.append(
                f"FOMC event today"
                " -- expect volatility around the announcement. "
                "Consider trimming position sizes or hedging with VIX calls."
            )
        if "pce" in name:
            tips.append(
                "PCE Price Index releases today"
                " -- the Fed's preferred inflation gauge. "
                "A hot print could reprice rate-cut expectations; "
                "consider hedging bond duration (TLT) and adding inflation protection (TIPS, GLD)."
            )
        if "gdp" in name:
            tips.append(
                "GDP releases today"
                " -- a weak print shifts sentiment toward defensives (XLU, XLP); "
                "a strong beat supports risk-on positioning in cyclicals (XLY, XLI)."
            )
        if "cpi" in name and "today" not in tips[-1] if tips else True:
            tips.append(
                "CPI releases today"
                " -- watch for a surprise in either direction. "
                "Hot print → TIPS and defensives; cool print → growth stocks and long bonds."
            )

    if not tips:
        tips.append(
            "No strong directional signals this morning -- maintain current allocations "
            "and watch for intraday cues."
        )

    return tips[:6]  # cap at 6 tips


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
    )
    tips         = generate_daybreak_positioning_tips(us_indices, futures,
                                                       yesterday_events, today_events)

    # ── Editorial overrides (stored in fixture under "editorial" key) ──────────
    editorial = raw.get("editorial", {})
    if editorial.get("narrative_suffix"):
        narrative = narrative.rstrip() + " " + editorial["narrative_suffix"]
    if editorial.get("plain_summary"):
        plain_summary = editorial["plain_summary"]
    for extra_tip in editorial.get("extra_tips", []):
        tips.append(extra_tip)

    # Best / worst across all US entries (exclude non-table entries like WTI Crude Oil)
    all_us = [i for i in us_indices if i["daily_pct"] is not None and i.get("table", True)]
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
