# Market Day Break — {{ date }}

*Daily Edition · Market intelligence at the open*

---

## Morning Brief

{{ narrative }}

---

## What This Means

{{ plain_summary }}

---
{% if market_news %}
## Market-Moving Headlines

| # | Headline | Source |
|---|----------|--------|
{% for item in market_news -%}
| {{ loop.index }} | [{{ item.headline }}]({{ item.url }}) | {{ item.source }} |
{% endfor %}
---
{% endif %}
## US Market Close

| Index | Close | Daily % |
|-------|-------|---------|
{% for idx in us_indices -%}
| {{ idx.name }} | {% if idx.close is not none %}{{ "%.2f"|format(idx.close) }}{% if idx.get('is_yield') %}%{% endif %}{% else %}--{% endif %} | {% if idx.get('is_yield') %}{% if idx.get('yield_change_bps') is not none %}{{ "%+.0f"|format(idx.yield_change_bps) }} bps{% else %}--{% endif %}{% elif idx.daily_pct is not none %}{{ "%+.2f"|format(idx.daily_pct) }}%{% else %}--{% endif %} |
{% endfor %}

**Best:** {{ us_best.name }} ({{ "%+.2f"|format(us_best.daily_pct) }}%) | **Worst:** {{ us_worst.name }} ({{ "%+.2f"|format(us_worst.daily_pct) }}%)

---

## Overnight Markets

### Asia-Pacific (Closed)

| Index | Close | Daily % |
|-------|-------|---------|
{% for idx in intl_indices if idx.region == 'Asia-Pacific' -%}
| {{ idx.name }} | {% if idx.close is not none %}{{ "%.2f"|format(idx.close) }}{% else %}--{% endif %} | {% if idx.daily_pct is not none %}{{ "%+.2f"|format(idx.daily_pct) }}%{% else %}--{% endif %} |
{% endfor %}

### Europe

| Index | Price | Daily % | Session |
|-------|-------|---------|---------|
{% for idx in intl_indices if idx.region == 'Europe' -%}
| {{ idx.name }} | {% if idx.close is not none %}{{ "%.2f"|format(idx.close) }}{% else %}--{% endif %} | {% if idx.daily_pct is not none %}{{ "%+.2f"|format(idx.daily_pct) }}%{% else %}--{% endif %} | {{ idx.session_note }} |
{% endfor %}

---

## Currencies & Safe Havens

| Pair | Rate | Daily % |
|------|------|---------|
{% for fx in fx_rates -%}
| {{ fx.name }} | {% if fx.rate is not none %}{{ "%.4f"|format(fx.rate) }}{% else %}--{% endif %} | {% if fx.daily_pct is not none %}{{ "%+.2f"|format(fx.daily_pct) }}%{% else %}--{% endif %} |
{% endfor %}

---

## Pre-Market Futures

| Contract | Price | Daily % |
|----------|-------|---------|
{% for fut in futures -%}
| {{ fut.name }} | {% if fut.price is not none %}{{ "%.2f"|format(fut.price) }}{% else %}--{% endif %} | {% if fut.daily_pct is not none %}{{ "%+.2f"|format(fut.daily_pct) }}%{% else %}--{% endif %} |
{% endfor %}

---

## What Moved Markets Yesterday

| Event | Actual | Expected | Previous | Surprise |
|-------|--------|----------|----------|---------|
{% for ev in yesterday_events -%}
| {{ ev.event }} | {{ ev.actual }}{{ ev.get('unit', '') }} | {{ ev.expected }}{{ ev.get('unit', '') }} | {{ ev.previous }}{{ ev.get('unit', '') }} | {{ ev.get('surprise', 'neutral') | title }} |
{% else -%}
| *No major events* | | | | |
{% endfor %}

---

## Today's Watch List

| Time (EST) | Event | Importance | Expected |
|-----------|-------|------------|---------|
{% for ev in today_events -%}
| {{ ev.get('time_est', '--') or '--' }} | {{ ev.event }} | {% if ev.get('importance', 0) >= 3 %}High{% elif ev.get('importance', 0) == 2 %}Medium{% else %}Low{% endif %} | {{ ev.get('expected', '--') }}{{ ev.get('unit', '') }} |
{% else -%}
| | *No high-importance events today* | | |
{% endfor %}

---

## Positioning Notes

{% for tip in tips -%}
- {{ tip }}
{% endfor %}

---

*Framework Foundry — Daily Edition. For informational purposes only. Not investment advice.*
