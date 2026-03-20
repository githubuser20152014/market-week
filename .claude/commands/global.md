Run the Framework Foundry Global Investor Edition generator with Perplexity MCP as the primary data source and review checkpoints before publishing.

**Step 0 — Fetch verified weekly prices via Perplexity:**

1. Determine DATE from $ARGUMENTS (or today if empty).
2. Check if all three fixtures exist:
   - `weekly-newsletter/fixtures/global_equity_DATE.json`
   - `weekly-newsletter/fixtures/global_fx_DATE.json`
   - `weekly-newsletter/fixtures/global_commodity_DATE.json`
   If all three exist, skip to Step 1.
3. Run four targeted Perplexity queries using the `mcp__perplexity__perplexity_ask` tool with `search_recency_filter: "week"`:

   **Query 1 — US equity indices (weekly):**
   > What were the Friday closing prices and weekly % changes for the week ending [DATE] for: S&P 500, Dow Jones, Nasdaq Composite, Russell 2000, 10-Year Treasury yield, USD Index (DXY), and VIX? Return JSON only with keys: sp500, sp500_weekly_pct, dow, dow_weekly_pct, nasdaq, nasdaq_weekly_pct, russell2000, russell2000_weekly_pct, ten_year_yield, ten_year_yield_week_start, usd_index, usd_index_weekly_pct, vix, vix_weekly_pct. Use 4 PM ET Friday close. Yield as percentage (e.g. 4.32). For ten_year_yield_week_start, return the Monday open yield.

   **Query 2 — International equity indices (weekly):**
   > What were the Friday closing prices and weekly % changes for the week ending [DATE] for: DAX, FTSE 100, CAC 40, Euro Stoxx 50, Nikkei 225, Hang Seng, ASX 200, MSCI Emerging Markets (EEM)? Return JSON only with keys: dax, dax_weekly_pct, ftse100, ftse100_weekly_pct, cac40, cac40_weekly_pct, eurostoxx50, eurostoxx50_weekly_pct, nikkei, nikkei_weekly_pct, hang_seng, hang_seng_weekly_pct, asx200, asx200_weekly_pct, msci_em, msci_em_weekly_pct. Use local market Friday close.

   **Query 3 — FX rates (weekly):**
   > What were the FX closing rates and weekly % changes for the week ending [DATE] for: EUR/USD, GBP/USD, JPY/USD (not USD/JPY — express as yen per dollar inverted, e.g. 0.00667 for USD/JPY of 150), AUD/USD, CHF/USD? Return JSON only with keys: eurusd, eurusd_weekly_pct, gbpusd, gbpusd_weekly_pct, jpyusd, jpyusd_weekly_pct, audusd, audusd_weekly_pct, chfusd, chfusd_weekly_pct. Use Friday 5 PM ET rates.

   **Query 4 — Commodities + US 30Y yield (weekly):**
   > What were the Friday closing prices and weekly % changes for the week ending [DATE] for: WTI Crude Oil, Natural Gas (Henry Hub), Gold (spot or front-month futures), Silver (spot or front-month futures), US 30-Year Treasury yield? Return JSON only with keys: wti_crude, wti_crude_weekly_pct, nat_gas, nat_gas_weekly_pct, gold, gold_weekly_pct, silver, silver_weekly_pct, us_30y_yield, us_30y_yield_week_start. For us_30y_yield_week_start, return the Monday open yield.

4. Apply sanity bounds check. Flag any value outside these ranges and ask the user to confirm or correct before proceeding:

   | Asset | Min | Max |
   |-------|-----|-----|
   | S&P 500 | 3,000 | 8,000 |
   | Dow | 20,000 | 55,000 |
   | Nasdaq | 8,000 | 25,000 |
   | Nikkei | 20,000 | 60,000 |
   | Gold | 1,500 | 6,000 |
   | WTI Crude | 40 | 200 |
   | 10Y Yield | 0.5 | 8.0 |
   | US 30Y Yield | 0.5 | 8.0 |
   | EUR/USD | 0.80 | 1.50 |
   | JPY/USD | 0.004 | 0.013 |
   | VIX | 9 | 80 |

   - If a price is out of bounds: show the flagged value and ask the user to confirm or correct it.
   - If Perplexity can't find a specific price: fall back to yfinance for that asset only.
   - If Perplexity is entirely unavailable: skip to Step 1 and pass `--live` to the generator.

5. Build the three fixtures by running:

   ```bash
   python weekly-newsletter/data/build_global_perplexity_fixtures.py \
       --date DATE \
       --prices 'JSON'
   ```

   Where `JSON` is a single-line JSON string with three keys — `"equity"`, `"fx"`, `"commodities"` — combining data from all four Perplexity queries. Use `null` for any price that could not be found.

   Example shape:
   ```json
   {
     "equity": {
       "sp500": 5500, "sp500_weekly_pct": -0.8,
       "dow": 44000, "dow_weekly_pct": -0.5,
       "nasdaq": 18000, "nasdaq_weekly_pct": -1.2,
       "russell2000": 2100, "russell2000_weekly_pct": -1.5,
       "ten_year_yield": 4.35, "ten_year_yield_week_start": 4.28,
       "usd_index": 104.2, "usd_index_weekly_pct": 0.3,
       "vix": 18.5, "vix_weekly_pct": 5.2,
       "dax": 22000, "dax_weekly_pct": 0.8,
       "ftse100": 9800, "ftse100_weekly_pct": -0.2,
       "cac40": 7600, "cac40_weekly_pct": 0.5,
       "eurostoxx50": 5400, "eurostoxx50_weekly_pct": 0.6,
       "nikkei": 54000, "nikkei_weekly_pct": -1.5,
       "hang_seng": 25000, "hang_seng_weekly_pct": 0.3,
       "asx200": 8200, "asx200_weekly_pct": -0.4,
       "msci_em": 1100, "msci_em_weekly_pct": 0.2
     },
     "fx": {
       "eurusd": 1.08, "eurusd_weekly_pct": 0.5,
       "gbpusd": 1.27, "gbpusd_weekly_pct": 0.3,
       "jpyusd": 0.00667, "jpyusd_weekly_pct": -0.2,
       "audusd": 0.63, "audusd_weekly_pct": 0.1,
       "chfusd": 1.12, "chfusd_weekly_pct": 0.4
     },
     "commodities": {
       "wti_crude": 72.5, "wti_crude_weekly_pct": -2.1,
       "nat_gas": 2.8, "nat_gas_weekly_pct": 1.5,
       "gold": 3200, "gold_weekly_pct": 0.8,
       "silver": 32.5, "silver_weekly_pct": 1.2,
       "us_30y_yield": 4.65, "us_30y_yield_week_start": 4.58
     }
   }
   ```

   The script automatically computes implied week-open prices from close + weekly_pct, builds synthetic OHLCV arrays, and saves all three fixtures. Sets `generation_source = "perplexity"` is implied by the fixture context (not a field in the weekly fixtures).

**Step 1 — Generate the Markdown only:**

```bash
cd weekly-newsletter && python generate_global_newsletter.py --date DATE
```

Because Step 0 already wrote the fixtures, the generator will detect them and run without `--live`.

After running, read the generated Markdown file at `weekly-newsletter/output/global_newsletter_DATE.md` and display its full contents to the user for review.

**Step 2 — Review checkpoint:**

Ask the user:
> "Here's the Global Investor Edition for [date]. Does everything look good, or would you like any changes before I publish?"

Wait for the user's response. If they request changes, edit the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Publish (only after user confirms content):**

```bash
bash weekly-newsletter/publish_weekly.sh DATE --global-only --publish
```

This rebuilds the static site, commits the fixtures and outputs, and pushes to GitHub Pages.

**Step 4 — Send email (only after user confirms):**

```bash
cd weekly-newsletter && python send_email.py --edition global --date DATE
```

If $ARGUMENTS is empty, use today's date for all steps.
