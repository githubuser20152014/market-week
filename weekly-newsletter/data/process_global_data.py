"""Process global equity/FX/commodity data and generate LLM narrative."""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path


# ── Weekly % computation ──────────────────────────────────────────────────────

def _weekly_pct(data):
    if len(data) < 2:
        return None
    first_open = data[0]["open"]
    last_close = data[-1]["close"]
    if first_open == 0:
        return None
    return round(((last_close - first_open) / first_open) * 100, 2)


def _week_range(data):
    if not data:
        return None, None
    return min(d["low"] for d in data), max(d["high"] for d in data)


# ── Equity processing ─────────────────────────────────────────────────────────

_US_NAMES    = {"S&P 500", "Dow Jones", "Nasdaq", "Russell 2000"}
_EU_NAMES    = {"DAX", "FTSE 100", "CAC 40", "Euro Stoxx 50"}
_APAC_NAMES  = {"Nikkei 225", "Hang Seng", "ASX 200", "MSCI EM"}
_FI_NAMES    = {"10Y Treasury", "USD Index"}
_VIX_NAME    = "VIX"

# Yield instruments — report bps change instead of %
_YIELD_NAMES = {"10Y Treasury", "US 30Y"}


def _make_index_entry(name, info):
    data   = info.get("data", [])
    last   = data[-1] if data else {}
    pct    = _weekly_pct(data)
    wl, wh = _week_range(data)
    entry  = {
        "name":       name,
        "symbol":     info.get("symbol", ""),
        "region":     info.get("region", ""),
        "etf_proxy":  info.get("etf_proxy", ""),
        "close":      last.get("close"),
        "weekly_pct": pct,
        "week_low":   wl,
        "week_high":  wh,
    }
    if name in _YIELD_NAMES:
        entry["is_yield"] = True
        entry["yield_change_bps"] = round((last.get("close", 0) - data[0].get("open", 0)) * 100, 1) if len(data) >= 2 else None
    return entry


def process_global_equity_data(raw):
    """Split raw equity dict into us_indices, eu_indices, apac_indices, fixed_income, vix.

    Returns:
        dict with keys: us_indices, eu_indices, apac_indices, fixed_income, vix
        Each value is a list of index entry dicts.
    """
    us_indices   = []
    eu_indices   = []
    apac_indices = []
    fixed_income = []
    vix          = None

    for name, info in raw.items():
        entry = _make_index_entry(name, info)
        if name == _VIX_NAME:
            vix = entry
        elif name in _US_NAMES:
            us_indices.append(entry)
        elif name in _EU_NAMES:
            eu_indices.append(entry)
        elif name in _APAC_NAMES:
            apac_indices.append(entry)
        elif name in _FI_NAMES:
            fixed_income.append(entry)

    # Sort each group best→worst by weekly_pct (treat None as 0 for sorting)
    for lst in (us_indices, eu_indices, apac_indices, fixed_income):
        lst.sort(key=lambda x: (x["weekly_pct"] or 0), reverse=True)

    return {
        "us_indices":   us_indices,
        "eu_indices":   eu_indices,
        "apac_indices": apac_indices,
        "fixed_income": fixed_income,
        "vix":          vix,
    }


# ── FX processing ─────────────────────────────────────────────────────────────

def process_global_fx_data(raw):
    """Compute weekly % change for each FX pair.

    Returns:
        List of dicts with: name, symbol, etf_proxy, rate, weekly_pct
    """
    results = []
    for name, info in raw.items():
        data = info.get("data", [])
        last = data[-1] if data else {}
        results.append({
            "name":       name,
            "symbol":     info.get("symbol", ""),
            "etf_proxy":  info.get("etf_proxy", ""),
            "rate":       last.get("close"),
            "weekly_pct": _weekly_pct(data),
        })
    results.sort(key=lambda x: (x["weekly_pct"] or 0), reverse=True)
    return results


# ── Commodity processing ──────────────────────────────────────────────────────

def process_global_commodity_data(raw):
    """Compute weekly % change for each commodity.

    Returns:
        List of dicts with: name, symbol, etf_proxy, close, weekly_pct, is_yield (for 30Y)
    """
    results = []
    for name, info in raw.items():
        data   = info.get("data", [])
        last   = data[-1] if data else {}
        wl, wh = _week_range(data)
        entry  = {
            "name":       name,
            "symbol":     info.get("symbol", ""),
            "etf_proxy":  info.get("etf_proxy", ""),
            "close":      last.get("close"),
            "weekly_pct": _weekly_pct(data),
            "week_low":   wl,
            "week_high":  wh,
        }
        if name in _YIELD_NAMES:
            entry["is_yield"] = True
            entry["yield_change_bps"] = round((last.get("close", 0) - data[0].get("open", 0)) * 100, 1) if len(data) >= 2 else None
        results.append(entry)
    results.sort(key=lambda x: (x["weekly_pct"] or 0), reverse=True)
    return results


# ── Macro regime ──────────────────────────────────────────────────────────────

def compute_macro_regime(us_indices, fixed_income, vix):
    """Derive a simple macro regime snapshot.

    Returns:
        dict with keys: growth, inflation, rate_direction, risk_appetite
        Each value: {signal: "green"|"yellow"|"red", note: str}
    """
    # Growth: S&P 500 weekly %
    spx = next((i for i in us_indices if "S&P" in i["name"]), None)
    spx_pct = (spx["weekly_pct"] or 0) if spx else 0
    if spx_pct >= 1:
        growth = {"signal": "green",  "note": f"S&P 500 +{spx_pct:.1f}% - risk-on expansion"}
    elif spx_pct <= -1:
        growth = {"signal": "red",    "note": f"S&P 500 {spx_pct:.1f}% - contraction signal"}
    else:
        growth = {"signal": "yellow", "note": f"S&P 500 {spx_pct:+.1f}% - growth neutral"}

    # Rate direction: 10Y Treasury bps change
    tnx = next((i for i in fixed_income if "10Y" in i["name"]), None)
    bps = (tnx.get("yield_change_bps") or 0) if tnx else 0
    if bps >= 5:
        rate_dir = {"signal": "red",    "note": f"10Y +{bps:.0f} bps - tightening pressure"}
    elif bps <= -5:
        rate_dir = {"signal": "green",  "note": f"10Y {bps:.0f} bps - easing signal"}
    else:
        rate_dir = {"signal": "yellow", "note": f"10Y {bps:+.0f} bps - rates stable"}

    # Inflation proxy: rates rising fast = inflation concern
    if bps >= 10:
        inflation = {"signal": "red",    "note": "Rising yields signal inflation concern"}
    elif bps <= -10:
        inflation = {"signal": "green",  "note": "Falling yields suggest easing inflation"}
    else:
        inflation = {"signal": "yellow", "note": "Inflation expectations mixed"}

    # Risk appetite: VIX level
    vix_close = (vix["close"] or 20) if vix else 20
    if vix_close < 15:
        risk = {"signal": "green",  "note": f"VIX {vix_close:.1f} - low fear, risk-on"}
    elif vix_close > 25:
        risk = {"signal": "red",    "note": f"VIX {vix_close:.1f} - elevated fear, risk-off"}
    else:
        risk = {"signal": "yellow", "note": f"VIX {vix_close:.1f} - moderate uncertainty"}

    return {
        "growth":          growth,
        "inflation":       inflation,
        "rate_direction":  rate_dir,
        "risk_appetite":   risk,
    }


# ── News digest context ───────────────────────────────────────────────────────

_DIGEST_SECTIONS = ["Markets & Macro", "Global Events", "Major Events"]


def load_digest_context(data_date: str, digest_dir) -> str:
    """Extract causal-context sections from daily digests for the week ending data_date.

    Pulls only 'Markets & Macro', 'Global Events', and 'Major Events' from each
    Mon-Fri digest file. Returns empty string if digest_dir is None or files are absent.
    """
    if not digest_dir:
        return ""

    end = datetime.strptime(data_date, "%Y-%m-%d")
    trading_days = []
    for i in range(6, -1, -1):
        d = end - timedelta(days=i)
        if d.weekday() < 5:
            trading_days.append(d.strftime("%Y-%m-%d"))
    trading_days = trading_days[-5:]

    chunks = []
    for date_str in trading_days:
        path = Path(digest_dir) / f"{date_str}-digest.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for section in _DIGEST_SECTIONS:
            match = re.search(
                rf"(?:#+\s+[^\n]*{re.escape(section)}[^\n]*\n)(.*?)(?=\n#+\s|\Z)",
                text,
                re.DOTALL | re.IGNORECASE,
            )
            if match:
                chunks.append(f"### {date_str} - {section}\n{match.group(1).strip()}")

    return "\n\n".join(chunks)


# ── Claude API narrative ───────────────────────────────────────────────────────

_GLOBAL_SYSTEM_PROMPT = """\
You are the editor of Framework Foundry Weekly - Global Investor Edition, a premium \
weekly newsletter for serious ETF investors managing diversified global portfolios. \
Your voice is authoritative but accessible: sharp analysis, no jargon for jargon's sake, \
and always focused on what it means for a patient, macro-aware investor.

Em dashes (—) are banned. Replace with context-appropriate punctuation: colon for an \
elaboration ("here is the reason"), comma for a parenthetical aside, period where two \
thoughts stand alone as separate sentences.

STYLE RULES — apply to every output field without exception:
- No financial boilerplate. Banned phrases: "amid concerns", "market participants remain \
  cautious", "volatility persists", "investors digest", "risk sentiment". Name the \
  specific catalyst, actor, price move, or policy decision instead.
- one_trade_body must open with the signal or anomaly, not the action. \
  Wrong: "Consider going long FEZ if conditions hold." \
  Right: "European equities are holding a key support level into a rate-cut window."
- Voice mandate: portfolio manager briefing a colleague before the week opens. \
  Short sentences. Active voice. Named catalysts with exact figures. No hedging language.

If the input contains a non-empty "news_context" field, it holds excerpts from daily news \
digests (Markets & Macro, Global Events, Major Events sections) covering the same week as \
the market data. You MUST anchor causal explanations to specific events from news_context \
rather than inferring causality from price correlations alone. Name the geopolitical event, \
policy decision, or macro catalyst that actually drove the move. If news_context is empty \
or absent, construct the best narrative you can from market data, but note that causal \
context was limited.

You will receive structured JSON market data and must return a JSON object with exactly \
these 13 keys:

- big_theme_title: A punchy 6-10 word headline capturing the week's dominant macro theme.
- big_theme_body: 2-3 paragraphs. What was the biggest macro story? Why did it happen? \
  What does it tell us about the regime? Use **bold** for key facts and counterintuitive insights.
- equity_subtitle: 5-8 word punchy subtitle for the equity section (e.g. "Europe Leads While US Consolidates").
- equity_narrative: 2 paragraphs. Compare US, European, and Asia-Pacific markets. \
  What diverged, what converged, and what does that signal? Use **bold** for key data points.
- fx_subtitle: 5-8 word punchy subtitle for the currency section (e.g. "Dollar Slips, EM Gets Relief").
- fx_narrative: 1-2 paragraphs. What moved in currencies and why? What does USD strength/\
  weakness mean for global investors? Use **bold** for key moves.
- commodities_subtitle: 5-8 word punchy subtitle for the commodities section (e.g. "Oil Breaks, Gold Holds Its Ground").
- commodities_narrative: 1-2 paragraphs. Key moves in energy, metals. Any regime signals? \
  Use **bold** for the most important move.
- events_commentary: 1-2 paragraphs. Interpret the week's economic data releases. \
  Any surprises vs. expectations?
- next_week_commentary: 1 paragraph. What events next week matter most and why?
- one_trade_ticker: The single best ETF ticker for the week's highest-conviction trade (e.g. "FEZ").
- one_trade_direction: "Long" or "Short".
- one_trade_body: 2-3 paragraphs making the case for the trade, followed by two lines: \
  "**Confirms:** [specific price/data trigger that validates the trade]" and \
  "**Risk:** [specific scenario that invalidates it]". Use **bold** for emphasis. \
  Do not repeat the ticker or direction in the body - that appears in the heading.
- plain_summary: 4-6 short plain-English sentences. DO NOT start with "What it means for you" \
  or any heading — the heading is already in the template. Write directly to a patient, globally \
  diversified ETF investor who has 10 minutes. Name the specific risk or opportunity created by \
  this week's moves. Reference ETF tickers where relevant. Use **bold** for the 2-3 most \
  important facts. No bullet points - prose only.
- positioning: 3-5 bullet points (plain text, one per line starting with "- "). \
  Each bullet: **bold ETF ticker(s)** followed by the rationale. \
  Concrete, actionable ETF-level positioning suggestions based on the week's signals.
- positioning: 3-5 bullet points (plain text, one per line starting with "- "). \
  Each bullet: **bold ETF ticker(s)** followed by the rationale. \
  Concrete, actionable ETF-level positioning suggestions based on the week's signals.

Return ONLY valid JSON - no markdown fences, no extra keys, no commentary outside the JSON.
"""


def generate_global_narrative(equity_data, fx_data, commodity_data, econ, macro_regime, digest_context=""):
    """Call Claude API to generate narrative sections.

    Returns:
        dict with 8 narrative keys (falls back to placeholder strings on error).
    """
    _FALLBACK = {
        "big_theme_title":       "Markets Navigating Macro Crosscurrents",
        "big_theme_body":        "Global markets moved cautiously this week as investors weighed mixed signals from major economies.",
        "equity_subtitle":       "Regional Divergence Across US, Europe, and Asia-Pacific",
        "equity_narrative":      "Equity markets showed regional divergence across US, Europe, and Asia-Pacific.",
        "fx_subtitle":           "Dollar Steady as Rate Expectations Shift",
        "fx_narrative":          "Currency markets reflected shifting rate expectations and risk sentiment.",
        "commodities_subtitle":  "Energy and Metals Respond to Global Demand Signals",
        "commodities_narrative": "Commodity prices responded to global demand signals and USD movements.",
        "events_commentary":     "Economic data releases were broadly in line with expectations.",
        "next_week_commentary":  "Key data releases next week will provide further clarity on the macro outlook.",
        "one_trade_ticker":      "EFA",
        "one_trade_direction":   "Long",
        "one_trade_body":        "International developed markets offer diversification away from US-centric risk.\n\n**Confirms:** EFA holds above prior week's close with dollar weakness continuing.\n**Risk:** Dollar reverses sharply higher on strong US data, compressing international returns.",
        "plain_summary":         "This week's key risk for global portfolios is energy-driven inflation. Hold your positions and watch next week's data before making changes.",
        "positioning":           "- Maintain diversified global ETF exposure\n- Monitor rate sensitive sectors\n- Watch USD for EM signals",
    }

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set — using placeholder narrative.")
        return _FALLBACK

    # Build the user message payload
    payload = {
        "macro_regime":   macro_regime,
        "us_indices":     equity_data["us_indices"],
        "eu_indices":     equity_data["eu_indices"],
        "apac_indices":   equity_data["apac_indices"],
        "fixed_income":   equity_data["fixed_income"],
        "vix":            equity_data["vix"],
        "fx":             fx_data,
        "commodities":    commodity_data,
        "econ_events":    econ,
        "news_context":   digest_context,
    }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=_GLOBAL_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(payload, default=str),
                }
            ],
        )
        raw_text = response.content[0].text.strip()
        # Strip markdown fences if present
        raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text).strip()
        result = json.loads(raw_text)
        # Ensure all 8 keys present
        for k, v in _FALLBACK.items():
            result.setdefault(k, v)
        return result
    except Exception as e:
        print(f"WARNING: Claude API call failed ({e}) — using placeholder narrative.")
        return _FALLBACK


# ── Full context assembly ─────────────────────────────────────────────────────

def build_global_template_context(
    equity_data, fx_data, commodity_data, econ, date_str,
    digest_dir=None, data_date=None,
):
    """Assemble the full context dict for Jinja2 / HTML rendering.

    Args:
        equity_data:    output of process_global_equity_data()
        fx_data:        output of process_global_fx_data()
        commodity_data: output of process_global_commodity_data()
        econ:           dict with 'past_week' and 'upcoming_week' lists
        date_str:       YYYY-MM-DD

    Returns:
        dict ready for template rendering.
    """
    macro_regime = compute_macro_regime(
        equity_data["us_indices"],
        equity_data["fixed_income"],
        equity_data["vix"],
    )

    digest_context = load_digest_context(data_date or date_str, digest_dir)
    if digest_context:
        print(f"Digest context loaded ({len(digest_context)} chars from {data_date or date_str} week).")

    narrative = generate_global_narrative(
        equity_data, fx_data, commodity_data, econ, macro_regime, digest_context
    )

    # Flatten all equities for the data appendix
    all_equities = (
        equity_data["us_indices"]
        + equity_data["eu_indices"]
        + equity_data["apac_indices"]
    )

    def _clean(text):
        """Strip em dashes and stray heading echoes from LLM output fields."""
        if not isinstance(text, str):
            return text
        import re as _re
        text = text.replace("—", "-")
        # Remove echo of "What it means for you" heading if LLM included it
        text = _re.sub(r"^What it means for you\s*\n*", "", text, flags=_re.IGNORECASE)
        return text.strip()

    def _clean_positioning(val):
        """Coerce positioning to a newline-joined string; sweep em dashes."""
        if isinstance(val, list):
            val = "\n".join(str(item) for item in val)
        return _clean(val)

    return {
        "date":             date_str,
        "date_display":     _fmt_date(date_str),
        # Macro
        "macro_regime":     macro_regime,
        # Narrative sections (from LLM)
        "big_theme_title":        _clean(narrative["big_theme_title"]),
        "big_theme_body":         _clean(narrative["big_theme_body"]),
        "equity_subtitle":        _clean(narrative["equity_subtitle"]),
        "equity_narrative":       _clean(narrative["equity_narrative"]),
        "fx_subtitle":            _clean(narrative["fx_subtitle"]),
        "fx_narrative":           _clean(narrative["fx_narrative"]),
        "commodities_subtitle":   _clean(narrative["commodities_subtitle"]),
        "commodities_narrative":  _clean(narrative["commodities_narrative"]),
        "events_commentary":      _clean(narrative["events_commentary"]),
        "next_week_commentary":   _clean(narrative["next_week_commentary"]),
        "one_trade_ticker":       _clean(narrative["one_trade_ticker"]),
        "one_trade_direction":    _clean(narrative["one_trade_direction"]),
        "one_trade_body":         _clean(narrative["one_trade_body"]),
        "plain_summary":          _clean(narrative.get("plain_summary", "")),
        "positioning":            _clean_positioning(narrative["positioning"]),
        # Market data for appendix tables
        "us_indices":    equity_data["us_indices"],
        "eu_indices":    equity_data["eu_indices"],
        "apac_indices":  equity_data["apac_indices"],
        "fixed_income":  equity_data["fixed_income"],
        "vix":           equity_data["vix"],
        "fx":            fx_data,
        "commodities":   commodity_data,
        # Economic calendar
        "past_events":     econ.get("past_week", []),
        "upcoming_events": econ.get("upcoming_week", []),
        # All equities for flat iteration
        "all_equities": all_equities,
    }


def _fmt_date(date_str):
    from datetime import datetime
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{d.strftime('%B')} {d.day}, {d.year}"
    except ValueError:
        return date_str
