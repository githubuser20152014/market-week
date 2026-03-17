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
    """Scene-setter intro for The Brief — 2–3 punchy sentences, no raw data list.

    Sets mood (direction + context clues) without repeating numbers that appear
    in plain_summary. Think: newspaper lede, not a Bloomberg terminal recap.
    """
    sp       = next((i for i in us_indices if "S&P"      in i["name"]), None)
    gold     = next((i for i in us_indices if i["name"] == "Gold"), None)
    treasury = next((i for i in us_indices if "Treasury" in i["name"]), None)
    eur_usd  = next((f for f in fx if "EUR" in f["name"]), None)

    fut_with_data  = [f for f in futures if f.get("daily_pct") is not None]
    apac_entries   = [i for i in intl_indices if i.get("region") == "Asia-Pacific"
                      and i.get("daily_pct") is not None]

    # ── Sentence 1: US stocks — direction with personality ────────────────────
    if not sp or sp.get("daily_pct") is None:
        return "Market data unavailable for yesterday's session."

    pct = sp["daily_pct"]
    if pct <= -2.0:
        lede = "Stocks had a bad day"
    elif pct <= -1.0:
        lede = "Stocks sold off"
    elif pct < -0.3:
        lede = "Stocks slipped"
    elif pct < 0.3:
        lede = "Stocks went nowhere in particular"
    elif pct < 1.0:
        lede = "Stocks edged higher"
    elif pct < 2.0:
        lede = "Stocks had a solid session"
    else:
        lede = "Stocks ran"

    # ── Cross-asset color: what else was happening ────────────────────────────
    gold_up  = gold and gold.get("daily_pct") is not None and gold["daily_pct"] > 0.2
    gold_dn  = gold and gold.get("daily_pct") is not None and gold["daily_pct"] < -0.2
    tsy_dn   = (treasury and treasury.get("yield_change_bps") is not None
                and treasury["yield_change_bps"] < -3)
    tsy_up   = (treasury and treasury.get("yield_change_bps") is not None
                and treasury["yield_change_bps"] > 3)
    # EUR/USD down = dollar up (dollar strengthened vs euro)
    dollar_up = eur_usd and eur_usd.get("daily_pct") is not None and eur_usd["daily_pct"] < -0.1

    context_note = ""
    if pct < -0.3:
        if gold_up and tsy_dn:
            context_note = ". Investors rotated into safe havens — gold and bonds both got the call"
        elif gold_up and not tsy_dn:
            context_note = ". Gold played its safe-haven role. Bonds sat this one out"
        elif tsy_up and pct < -0.5:
            context_note = ". Neither stocks nor bonds offered shelter — a tough session to hide in"
        elif dollar_up and not gold_up:
            context_note = ". Gold didn't play its safe-haven role yesterday — the dollar got the call instead"
        else:
            context_note = ". Sentiment stayed cautious"
    elif pct > 0.3:
        if gold_dn and tsy_up:
            context_note = ". Money rotated back into risk assets — the classic risk-on signal"
        elif tsy_up:
            context_note = ". Rising yields kept the rally measured"
        else:
            context_note = ". Risk appetite improved"

    sentence1 = lede + context_note + "."

    # ── Sentence 2: Futures/overnight signal ──────────────────────────────────
    sentence2 = ""
    if fut_with_data:
        all_green = all(f["daily_pct"] >= 0 for f in fut_with_data)
        all_red   = all(f["daily_pct"] <  0 for f in fut_with_data)
        if all_green:
            sentence2 = "Futures are pointing to a firmer open."
        elif all_red:
            sentence2 = "Futures are in the red. Cautious start expected."
        else:
            sentence2 = "Futures aren't giving a clear read. We'll find out at the open."
    elif apac_entries:
        apac_up = sum(1 for i in apac_entries if i["daily_pct"] >= 0)
        if apac_up == len(apac_entries):
            sentence2 = "Asia-Pacific closed higher overnight — a tentatively positive handoff."
        elif apac_up == 0:
            sentence2 = "Asia-Pacific closed lower overnight. Adds to the cautious tone."
        else:
            sentence2 = "Overnight markets were mixed. No clean signal either way."

    parts = [sentence1]
    if sentence2:
        parts.append(sentence2)
    return " ".join(parts)


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
        tone = "Stocks had a bad day"
    elif pct <= -1.0:
        tone = "Stocks sold off"
    elif pct < 0:
        tone = "Stocks slipped"
    elif pct >= 2.0:
        tone = "Stocks ran"
    elif pct >= 1.0:
        tone = "Stocks had a solid session"
    else:
        tone = "Stocks edged higher"

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
            sentence += " Broad selloff — all four major indices closed in the red."
        elif pct > 0 and all_up:
            sentence += " Broad-based. All four major indices closed green."
        elif pct < 0:
            up_count = sum(1 for c in comp_list if c["daily_pct"] > 0)
            if up_count:
                sentence += (
                    f" Worth noting: {up_count} of the other major indices stayed positive."
                    " This looks more like rotation than broad risk-off selling."
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
        sentence += f" Elsewhere: {cross_str}."

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
        para = f"**Geopolitics ran the session yesterday.** {geo_headline}."
        if "hormuz" in geo_headline.lower() or ("oil" in geo_headline.lower() and oil_close and oil_close > 95):
            para += (
                " The Strait of Hormuz is the world's most important oil chokepoint —"
                " roughly 20% of global oil supply passes through it daily."
                " Any credible threat moves energy markets. That ripples into inflation"
                " expectations, transportation costs, and EM currencies."
            )
        elif "iran" in geo_headline.lower() or "israel" in geo_headline.lower():
            para += (
                " Middle East escalation raises the risk premium across oil, shipping,"
                " and global supply chains — even headlines that don't immediately"
                " disrupt flows move markets. Investors reprice tail risk first,"
                " ask questions later."
            )

        # Counter-intuitive gold move
        if gold_pct is not None and gold_pct < -0.3 and sp_pct is not None and sp_pct < 0:
            para += (
                f" Gold fell {abs(gold_pct):.2f}% alongside equities — worth flagging."
                " When gold drops with stocks, it's usually a signal that the dollar"
                " is the real safe-haven trade. Investors went to cash and USD, not bullion."
            )
            if tsy_bps is not None and abs(tsy_bps) < 3:
                para += (
                    " The 10-year yield barely moved either — no rotation into Treasuries."
                    " The flight-to-safety trade went straight to the dollar."
                )
        elif gold_pct is not None and gold_pct > 0.5 and sp_pct is not None and sp_pct < 0:
            para += (
                f" Gold gained {gold_pct:.2f}% as stocks fell — the classic risk-off"
                f" signal. Investors are actively rotating into safe havens."
            )
        parts.append(para)

    # Fed-led
    elif fed_score >= 2:
        if tsy_bps is not None and tsy_bps > 3 and tsy_close is not None and sp_pct is not None and sp_pct < 0:
            para = (
                f"**Bonds are saying: don't count on rate cuts.** Treasury yields climbed"
                f" {round(abs(tsy_bps))} bps to {tsy_close:.2f}% as investors repriced"
                f" the Fed's easing timeline. Higher yields make future earnings worth"
                f" less today — that compresses valuations, and growth stocks feel it most."
            )
            if nasdaq and nasdaq.get("daily_pct") is not None and nasdaq["daily_pct"] < (sp_pct or 0):
                para += (
                    f" The Nasdaq confirmed it: underperformed the S&P 500"
                    f" ({nasdaq['daily_pct']:+.2f}% vs. {sp_pct:+.2f}%)."
                    f" That's a yield-driven selloff doing exactly what it's supposed to do."
                )
            parts.append(para)
        else:
            parts.append(
                "**Fed expectations are shifting.** Rate-cut bets continued to move,"
                " creating uncertainty around the cost of capital and what equities are worth."
                " Not a crisis — just a market recalibrating."
            )

    # Trade-led
    elif trade_score >= 2 and trade_headline:
        para = f"**Trade policy was the culprit.** {trade_headline}."
        if sp_pct is not None and sp_pct < 0:
            para += (
                " Tariff headlines hit multinationals hardest."
                " Companies with significant overseas revenue or production face margin"
                " compression that's hard to hedge away. Not a new story."
                " Still moving markets."
            )
        parts.append(para)

    # Data-driven session
    elif econ_notes:
        note = econ_notes[0]
        para = f"**The data moved markets yesterday.** {note}."
        if tsy_bps is not None and abs(tsy_bps) >= 3 and tsy_close is not None:
            direction = "higher" if tsy_bps > 0 else "lower"
            para += (
                f" Bonds responded: the 10-year yield moved {direction}"
                f" {round(abs(tsy_bps))} bps to {tsy_close:.2f}%."
                f" That fed straight into equity valuations through the discount-rate channel."
            )
        parts.append(para)

    # Light-catalyst session
    elif sp_pct is not None and abs(sp_pct) < 0.75:
        parts.append(
            "**Nothing happened. That's the story.** No single data print or headline"
            " stood out as the driver — this is normal price discovery in a"
            " directionless tape. Low-conviction moves like this often reverse quickly."
            " File it as noise until proven otherwise."
        )

    # Yield-driven (fallback)
    elif tsy_bps is not None and abs(tsy_bps) >= 4 and tsy_close is not None:
        direction = "climbed" if tsy_bps > 0 else "fell"
        parts.append(
            f"**Bond yields {direction} {round(abs(tsy_bps))} bps to {tsy_close:.2f}%.**"
            f" {'Rising yields compress valuations — growth and rate-sensitive sectors feel it first.' if tsy_bps > 0 else 'Falling yields reduce the competition bonds pose to equities. Rate-sensitive sectors and growth stocks tend to benefit.'}"
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
            f"Dollar strength ({usd_pct:+.2f}%) is a quiet headwind for multinationals."
            f" S&P 500 large caps collect revenue abroad but report in USD —"
            f" that gap eats into earnings. GLD and commodity ETFs (DJP) face the same drag."
        )
    elif usd_pct is not None and usd_pct < -0.3:
        implications.append(
            f"Dollar weakness ({usd_pct:+.2f}%) is a tailwind for international equities"
            f" and commodities. EM-focused funds (EEM, VWO) and GLD tend to benefit"
            f" when the dollar softens."
        )

    # Oil above $100
    if oil_close is not None and oil_close > 100:
        watch_items.append("oil — above $100/bbl it starts pressuring consumer spending and complicating the Fed's inflation story")
        implications.append(
            f"WTI above $100/bbl is a macro drag that's hard to ignore."
            f" It raises input costs across the supply chain, keeps headline CPI sticky,"
            f" and makes the Fed's path to rate cuts harder to justify."
            f" Energy ETFs (XLE) are in focus — but geopolitical oil spikes can reverse"
            f" fast. Don't chase."
        )
    elif oil_pct is not None and oil_pct < -1.5:
        implications.append(
            f"Oil's {abs(oil_pct):.2f}% decline is a quiet tailwind for consumer-facing"
            f" sectors. Lower energy costs flow into margins for transportation (XTN),"
            f" retail (XRT), and airlines."
        )

    # Yield implications
    if tsy_bps is not None and tsy_bps > 4 and tsy_close is not None:
        watch_items.append(f"the 10-year yield — further moves above {tsy_close:.2f}% would widen the pressure on valuations")
        implications.append(
            f"At {tsy_close:.2f}%, the 10-year yield is real competition for equities."
            f" Growth-heavy portfolios (QQQ) are most exposed to further increases."
            f" If yields stay elevated, value and dividend-payers"
            f" (VTV, DVY, SCHD) have historically held up better."
        )
    elif tsy_bps is not None and tsy_bps < -4 and tsy_close is not None:
        implications.append(
            f"Falling yields ({tsy_close:.2f}% now) lift rate-sensitive sectors:"
            f" REITs (VNQ), utilities (XLU), and long-duration growth stocks."
            f" Ask whether the decline reflects growth fears — bad for cyclicals —"
            f" or simply easing inflation. The answer changes the trade."
        )

    # Geopolitical premium flag
    if geo_score >= 2:
        watch_items.append("geopolitical headlines — escalation or de-escalation will move oil, FX, and risk sentiment quickly")

    if gold_pct is not None and gold_pct < -0.5 and sp_pct is not None and sp_pct < 0:
        watch_items.append("gold — if risk-off sentiment re-intensifies, gold could recover sharply as the safe-haven trade catches up")

    # Fallback for quiet session
    if not implications:
        if sp_pct is not None and abs(sp_pct) < 0.5:
            implications.append(
                "Yesterday was quiet. Modest moves without a catalyst are noise, not signal."
                " No allocation changes warranted."
            )
        elif sp_pct is not None and sp_pct < 0:
            implications.append(
                "A sub-1% pullback isn't a signal. It's within normal volatility."
                " Hold course. Watch today's open before drawing conclusions."
            )

    parts = []
    if implications:
        lead = "**Here's what this means for your portfolio.**"
        parts.append(lead + " " + " ".join(implications))
    if watch_items:
        parts.append("**Watch:** " + "; ".join(watch_items) + ".")

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
                    " The market is calling yesterday a dip — not a trend."
                    " Whether buyers follow through at the open is the question."
                )
            else:
                open_call += (
                    " Futures are extending yesterday's gains. Risk-on momentum is intact."
                    " Watch for overextension if there's no fresh catalyst to justify it."
                )
        elif all_red:
            open_call = (
                f"**Pre-market is cautious** ({fut_detail})."
            )
            if sp_pct and sp_pct < 0:
                open_call += (
                    " Sellers are pushing again. The question is whether buyers show up — or don't."
                )
            else:
                open_call += (
                    " Despite a solid session yesterday, sellers are pushing back in pre-market."
                    " Early weakness that holds is a sign the rally needs to consolidate."
                )
        else:
            open_call = (
                f"**Futures are mixed** ({fut_detail})."
                " No conviction either way."
                " The first 30 minutes will be more informative than anything said before the bell."
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
                f"**{names_str} prints{time_str} — this is the risk event.**"
                f" A hot number pushes yields higher, kills rate-cut hopes, and hits"
                f" growth stocks (QQQ) hardest. A cool print does the opposite — lifts"
                f" long bonds (TLT) and tech. Either way: know where you stand"
                f" before this hits. Not after."
            )
        elif has_gdp and has_pce:
            gdp_name = next((n for n in event_names if "gdp" in n.lower()), "GDP")
            pce_name = next((n for n in event_names if "pce" in n.lower()), "PCE")
            parts.append(
                f"**{gdp_name} and {pce_name} both print{time_str}.**"
                f" Weak GDP + hot PCE is stagflation — the worst combination for equities."
                f" Strong GDP + tame PCE keeps the soft-landing story intact."
                f" Position before the print. Not after."
            )
        elif has_gdp:
            parts.append(
                f"**{names_str} prints{time_str}.**"
                f" A weak number moves sentiment toward defensives (XLU, XLP) and bonds."
                f" A strong beat supports cyclicals (XLY, XLI) and risk-on positioning."
            )
        elif has_jobs:
            parts.append(
                f"**{names_str} prints{time_str}.**"
                f" Strong jobs data complicates the Fed's rate-cut math and pushes yields higher."
                f" A weak print revives easing hopes. Position before the release."
            )
        else:
            verb = "print" if len(event_names) > 1 else "prints"
            parts.append(
                f"**{names_str} {verb}{time_str} today.**"
                f" Watch for a surprise — these releases move bonds and rate-sensitive sectors fast."
            )
    elif mid_today:
        names_str = ", ".join(e.get("event", "") for e in mid_today[:2])
        parts.append(
            f"**Light calendar today ({names_str}).**"
            f" Direction comes from news flow and overnight follow-through — not data."
            f" Fed commentary or a headline shock could reset everything quickly."
        )
    else:
        parts.append(
            "**No data today.** Markets trade on news flow, Fed speakers, and"
            " whatever the tape feels like."
            " Quiet data days can actually amplify headline-driven moves —"
            " less signal to anchor against."
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
                f"S&P 500 pulled back {abs(sp_pct):.2f}% with no major catalyst -- "
                "routine dip in an uptrend. Hold course; watch today's open for confirmation."
            )
        elif sp_pct is not None and sp_pct > 0.5:
            tips.append(
                f"S&P 500 gained {sp_pct:.2f}% yesterday -- no action needed. "
                "Watch for overextension if today gaps up further without a fresh catalyst."
            )
        else:
            tips.append(
                "No high-conviction signals today -- hold current allocations. "
                "Light calendar means headline risk drives the tape. Size positions accordingly."
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
    """Generate a 4-tweet thread for X (Twitter) from the daybreak context.

    Tweet 1: Hook + key index numbers + cross-asset snapshot
    Tweet 2: Why it happened — dominant theme + key signal
    Tweet 3: Positioning — pre-market + specific ETF tips
    Tweet 4: Link + hashtags

    Returns four blocks separated by '\\n---\\n', each ≤280 chars.
    Warns via UserWarning if any block exceeds the limit.
    """
    import warnings

    us_indices = context.get("us_indices") or []
    futures    = context.get("futures")    or []
    tips       = context.get("tips") or context.get("positioning_tips") or []
    news_items = context.get("news_items") or []
    plain_summary = context.get("plain_summary", "")

    sp      = next((i for i in us_indices if "S&P"     in i.get("name", "")), None)
    nasdaq  = next((i for i in us_indices if "Nasdaq"  in i.get("name", "")), None)
    dow     = next((i for i in us_indices if "Dow"     in i.get("name", "")), None)
    russell = next((i for i in us_indices if "Russell" in i.get("name", "")), None)
    gold    = next((i for i in us_indices if i.get("name") == "Gold"), None)
    oil     = next((i for i in us_indices if "WTI"     in i.get("name", "") or "Crude" in i.get("name", "")), None)
    treasury = next((i for i in us_indices if "Treasury" in i.get("name", "")), None)

    # ── Tweet 1: Hook + numbers ────────────────────────────────────────────────
    title = _generate_post_title(context)

    index_lines = []
    for idx in [sp, nasdaq, dow, russell]:
        if idx and idx.get("daily_pct") is not None and idx.get("close") is not None:
            short = {"S&P 500": "S&P", "Nasdaq": "Nasdaq", "Dow Jones": "Dow", "Russell 2000": "Russell"}.get(idx["name"], idx["name"])
            index_lines.append(f"{short} {idx['close']:,.0f} ({idx['daily_pct']:+.2f}%)")

    cross = []
    if gold and gold.get("daily_pct") is not None:
        cross.append(f"Gold {gold['daily_pct']:+.2f}%")
    if oil and oil.get("daily_pct") is not None and oil.get("close") is not None:
        cross.append(f"Oil ${oil['close']:.0f} ({oil['daily_pct']:+.2f}%)")
    if treasury and treasury.get("yield_change_bps") is not None and treasury.get("close") is not None:
        bps = round(treasury["yield_change_bps"])
        sign = "+" if bps >= 0 else ""
        cross.append(f"10Y {treasury['close']:.2f}% ({sign}{bps}bps)")

    us_best  = context.get("us_best")
    us_worst = context.get("us_worst")
    best_worst = ""
    if us_best and us_worst:
        best_worst = f"Best: {us_best['name']} ({us_best['daily_pct']:+.2f}%) | Worst: {us_worst['name']} ({us_worst['daily_pct']:+.2f}%)"

    t1_parts = []
    if title:
        t1_parts.append(title)
    if index_lines:
        t1_parts.append(" | ".join(index_lines))
    if cross:
        t1_parts.append("  ".join(cross))
    if best_worst:
        t1_parts.append(best_worst)
    t1_parts.append("🧵 1/4")
    tweet1 = "\n".join(t1_parts)

    # ── Tweet 2: Why it happened + going into today ────────────────────────────
    # Combine the "why" paragraph (para 2) with the pre-market signal from para 4
    paras = [p.strip() for p in plain_summary.split("\n\n") if p.strip()]
    why_para    = paras[1] if len(paras) > 1 else (paras[0] if paras else "")
    going_para  = paras[4] if len(paras) > 4 else (paras[3] if len(paras) > 3 else "")

    why_text = _strip_markdown(why_para)
    # Trim why to ~180 chars; pad with first sentence of "going into today" if room
    why_text = _trim_to_sentences(why_text, 180)
    going_text = ""
    if going_para:
        going_text = _trim_to_sentences(_strip_markdown(going_para), 120)
    combined = f"{why_text}\n\n{going_text}".strip() if going_text else why_text
    # Final trim to 240 chars total
    combined = _trim_to_sentences(combined, 240)
    tweet2 = f"{combined}\n\n🧵 2/4"

    # ── Tweet 3: Top positioning tip (full) ───────────────────────────────────
    # Include the first tip in full (Signal -- Action format, no truncation).
    # If the first tip alone exceeds 274 chars, trim to the nearest sentence.
    TWEET_BODY_LIMIT = 274  # 280 minus "🧵 3/4" + "\n\n"
    top_tip = _strip_markdown(tips[0]) if tips else ""
    if len(top_tip) > TWEET_BODY_LIMIT:
        top_tip = _trim_to_sentences(top_tip, TWEET_BODY_LIMIT)
    tweet3 = f"{top_tip}\n\n🧵 3/4" if top_tip else "See full positioning notes at frameworkfoundry.info/daily/\n\n🧵 3/4"

    # ── Tweet 4: Link ──────────────────────────────────────────────────────────
    tweet4 = "Full breakdown + positioning notes:\nframeworkfoundry.info/daily/\n\n#MacroInvesting #ETFs #MarketOpen\n\n🧵 4/4"

    TWEET_LIMIT = 280
    tweets = [tweet1, tweet2, tweet3, tweet4]
    for i, tweet in enumerate(tweets, start=1):
        if len(tweet) > TWEET_LIMIT:
            overage = len(tweet) - TWEET_LIMIT
            warnings.warn(
                f"X thread tweet {i}/4 is {len(tweet)} chars — {overage} over the 280-char limit. "
                "Trim before posting.",
                UserWarning,
                stacklevel=2,
            )

    return "\n---\n".join(tweets)


def _trim_to_sentences(text: str, max_chars: int) -> str:
    """Trim text to at most max_chars, breaking at the last complete sentence or clause."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Find the last clean break: sentence end or clause separator
    last_end = max(
        truncated.rfind(". "),
        truncated.rfind("! "),
        truncated.rfind("? "),
        truncated.rfind("; "),
    )
    if last_end > max_chars // 2:
        return truncated[:last_end + 1].strip()
    return truncated.rstrip(" ,;") + "…"


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
        f"*Full edition + raw data: [frameworkfoundry.info/daily/{context['date']}/data](https://frameworkfoundry.info/daily/{context['date']}/data)*\n\n*Framework Foundry · Unsubscribe*",
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
        "market_news":    process_market_news(market_news_raw)[:5],
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
