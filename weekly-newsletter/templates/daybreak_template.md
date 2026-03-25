# The Morning Brief — {{ date }}

*Daily Edition · Market intelligence at the open*

---

## The Brief

{{ narrative }}

{{ brief_body }}

---

## What it means for you

{{ investor_section }}

{% if one_trade %}
---

## The One Trade

**[{{ one_trade.ticker }}](https://finance.yahoo.com/quote/{{ one_trade.ticker }}) — {{ one_trade.direction }}**

*{{ one_trade.thesis }}*

**Confirms:** {{ one_trade.confirm }}
**Risk:** {{ one_trade.risk }}
{% endif %}
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
## Positioning Notes

{% for tip in tips -%}
- {{ tip }}
{% endfor %}

---

*Framework Foundry — Daily Edition. For informational purposes only. Not investment advice.*
