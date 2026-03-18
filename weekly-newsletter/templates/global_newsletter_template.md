# Framework Foundry Weekly — Global Investor Edition
## {{ date_display }}

---

## Page 1 — What Happened & Why

### {{ big_theme_title }}

{{ big_theme_body }}

---

### Macro Regime Snapshot

| Variable | Signal | Note |
|----------|--------|------|
| Growth | {{ macro_regime.growth.signal | upper }} | {{ macro_regime.growth.note }} |
| Inflation | {{ macro_regime.inflation.signal | upper }} | {{ macro_regime.inflation.note }} |
| Rate Direction | {{ macro_regime.rate_direction.signal | upper }} | {{ macro_regime.rate_direction.note }} |
| Risk Appetite | {{ macro_regime.risk_appetite.signal | upper }} | {{ macro_regime.risk_appetite.note }} |

---

### Equity Markets

{{ equity_narrative }}

---

### Currency Markets

{{ fx_narrative }}

---

### Commodities & Metals

{{ commodities_narrative }}

---

## Page 2 — Events & Positioning

### This Week's Economic Events

{{ events_commentary }}

---

### Next Week: What to Watch

{{ next_week_commentary }}

---

### Global Investor Positioning

{{ positioning }}

---

## Page 3 — Data Appendix

### US Equities

| Index | Close | Weekly % | Week Range |
|-------|-------|----------|------------|
{% for idx in us_indices -%}
| {{ idx.name }} | {{ "%.2f"|format(idx.close) if idx.close else "—" }} | {% if idx.is_yield is defined and idx.is_yield %}{{ "%+.0f bps"|format(idx.yield_change_bps) if idx.yield_change_bps is not none else "—" }}{% else %}{{ "%+.2f%%"|format(idx.weekly_pct) if idx.weekly_pct is not none else "—" }}{% endif %} | {{ "%.2f"|format(idx.week_low) if idx.week_low else "—" }} – {{ "%.2f"|format(idx.week_high) if idx.week_high else "—" }} |
{% endfor %}

### European Equities

| Index | Close | Weekly % | Week Range |
|-------|-------|----------|------------|
{% for idx in eu_indices -%}
| {{ idx.name }} | {{ "%.2f"|format(idx.close) if idx.close else "—" }} | {{ "%+.2f%%"|format(idx.weekly_pct) if idx.weekly_pct is not none else "—" }} | {{ "%.2f"|format(idx.week_low) if idx.week_low else "—" }} – {{ "%.2f"|format(idx.week_high) if idx.week_high else "—" }} |
{% endfor %}

### Asia-Pacific Equities

| Index | Close | Weekly % | Week Range |
|-------|-------|----------|------------|
{% for idx in apac_indices -%}
| {{ idx.name }} | {{ "%.2f"|format(idx.close) if idx.close else "—" }} | {{ "%+.2f%%"|format(idx.weekly_pct) if idx.weekly_pct is not none else "—" }} | {{ "%.2f"|format(idx.week_low) if idx.week_low else "—" }} – {{ "%.2f"|format(idx.week_high) if idx.week_high else "—" }} |
{% endfor %}

### Currencies (vs. USD)

| Pair | Rate | Weekly % |
|------|------|----------|
{% for fx in fx -%}
| {{ fx.name }} | {{ "%.4f"|format(fx.rate) if fx.rate else "—" }} | {{ "%+.2f%%"|format(fx.weekly_pct) if fx.weekly_pct is not none else "—" }} |
{% endfor %}

### Commodities & Fixed Income

| Asset | Close | Weekly % |
|-------|-------|----------|
{% for c in commodities -%}
| {{ c.name }} | {{ "%.2f"|format(c.close) if c.close else "—" }} | {% if c.is_yield is defined and c.is_yield %}{{ "%+.0f bps"|format(c.yield_change_bps) if c.yield_change_bps is not none else "—" }}{% else %}{{ "%+.2f%%"|format(c.weekly_pct) if c.weekly_pct is not none else "—" }}{% endif %} |
{% endfor %}

### Fixed Income

| Instrument | Close | Weekly Change |
|------------|-------|--------------|
{% for fi in fixed_income -%}
| {{ fi.name }} | {{ "%.2f"|format(fi.close) if fi.close else "—" }} | {% if fi.is_yield is defined and fi.is_yield %}{{ "%+.0f bps"|format(fi.yield_change_bps) if fi.yield_change_bps is not none else "—" }}{% else %}{{ "%+.2f%%"|format(fi.weekly_pct) if fi.weekly_pct is not none else "—" }}{% endif %} |
{% endfor %}

---

*Framework Foundry Weekly — Global Investor Edition. For informational purposes only. Not investment advice.*
