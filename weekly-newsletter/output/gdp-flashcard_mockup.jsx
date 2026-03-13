import { useState } from "react";

/* ── BRAND TOKENS (from Framework Foundry) ─────────────────────────────── */
const T = {
  navy:      "#0f1f3d",
  navyMid:   "#1a3260",
  accent:    "#4a7fb5",
  accentLt:  "#7aabda",
  gold:      "#c9a84c",
  goldLt:    "#e0c97a",
  white:     "#ffffff",
  offWhite:  "#f5f4f0",
  text:      "#1a1a2e",
  border:    "#ddd8cc",
  muted:     "#6b7280",
  green:     "#2a7d4f",
  red:       "#b91c1c",
  bg:        "#dde3ea",
};

/* ── MINI BAR CHART ─────────────────────────────────────────────────────── */
function MiniBarChart({ data }) {
  const max = Math.max(...data.map(d => d.value));
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", height: "72px" }}>
      {data.map((d, i) => {
        const isLast = i === data.length - 1;
        const pct = (d.value / max) * 100;
        const barColor = isLast ? T.red : T.accent;
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
            <span style={{
              fontSize: "9px",
              fontFamily: "'Raleway', sans-serif",
              fontWeight: "700",
              color: isLast ? T.red : T.accentLt,
              marginBottom: "3px",
              letterSpacing: "0.5px",
            }}>{d.value}%</span>
            <div style={{
              width: "100%",
              height: `${pct}%`,
              minHeight: "4px",
              background: isLast
                ? `linear-gradient(180deg, ${T.red}, #7f1111)`
                : `linear-gradient(180deg, ${T.accentLt}, ${T.accent})`,
              borderRadius: "1px 1px 0 0",
            }} />
            <span style={{
              fontSize: "8px",
              fontFamily: "'Raleway', sans-serif",
              fontWeight: "600",
              letterSpacing: "1px",
              color: isLast ? T.gold : "rgba(255,255,255,0.45)",
              marginTop: "5px",
              textTransform: "uppercase",
            }}>{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ── TREND BADGE ────────────────────────────────────────────────────────── */
function TrendBadge({ direction, label }) {
  const styles = {
    up:   { background: "#d4edda", color: "#155724" },
    down: { background: "#f8d7da", color: "#721c24" },
    flat: { background: "#e8e8e8", color: "#555" },
  };
  const arrows = { up: "↑", down: "↓", flat: "→" };
  return (
    <span style={{
      ...styles[direction],
      fontFamily: "'Raleway', sans-serif",
      fontSize: "9px",
      fontWeight: "700",
      letterSpacing: "1px",
      padding: "3px 8px",
      borderRadius: "2px",
    }}>
      {arrows[direction]} {label}
    </span>
  );
}

/* ── FLASHCARD ──────────────────────────────────────────────────────────── */
const GDP_QUARTERS = [
  { label: "Q1 '25", value: 2.4 },
  { label: "Q2 '25", value: 3.8 },
  { label: "Q3 '25", value: 4.4 },
  { label: "Q4 '25", value: 1.4 },
];

export default function GDPFlashcard() {
  const [flipped, setFlipped] = useState(false);

  return (
    <div style={{
      minHeight: "100vh",
      background: T.bg,
      fontFamily: "'Source Serif 4', Georgia, serif",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "48px 20px",
      gap: "0",
    }}>
      <link
        href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;1,8..60,300&display=swap"
        rel="stylesheet"
      />

      {/* ── Page chrome that mirrors the site ── */}
      <div style={{
        width: "100%",
        maxWidth: "820px",
        background: T.white,
        boxShadow: "0 8px 48px rgba(0,0,0,0.18)",
      }}>

        {/* HEADER */}
        <header style={{
          background: T.navy,
          position: "relative",
          overflow: "hidden",
        }}>
          {/* grid texture */}
          <div style={{
            position: "absolute", inset: 0,
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)
            `,
            backgroundSize: "28px 28px",
          }} />
          <div style={{
            position: "relative",
            display: "flex",
            alignItems: "center",
            padding: "22px 40px 18px",
            gap: "16px",
          }}>
            {/* logo icon */}
            <svg width="52" height="52" viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="34" fill="none" stroke="white" strokeWidth="1.4" opacity="0.85"/>
              <line x1="10" y1="30" x2="70" y2="30" stroke="white" strokeWidth="0.7" opacity="0.3"/>
              <line x1="8"  y1="40" x2="72" y2="40" stroke="white" strokeWidth="0.7" opacity="0.3"/>
              <line x1="10" y1="50" x2="70" y2="50" stroke="white" strokeWidth="0.7" opacity="0.3"/>
              <line x1="30" y1="8"  x2="30" y2="72" stroke="white" strokeWidth="0.7" opacity="0.3"/>
              <line x1="40" y1="6"  x2="40" y2="74" stroke="white" strokeWidth="0.7" opacity="0.3"/>
              <line x1="50" y1="8"  x2="50" y2="72" stroke="white" strokeWidth="0.7" opacity="0.3"/>
              <line x1="18" y1="62" x2="62" y2="18" stroke="#c9a84c" strokeWidth="2.2" strokeLinecap="round"/>
              <circle cx="40" cy="40" r="3" fill="#c9a84c"/>
            </svg>
            <div>
              <span style={{
                display: "block",
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: "26px", fontWeight: "600",
                letterSpacing: "4px", color: T.white, lineHeight: 1,
              }}>FRAMEWORK</span>
              <span style={{
                display: "block",
                fontFamily: "'Raleway', sans-serif",
                fontSize: "12px", fontWeight: "300",
                letterSpacing: "11px", color: T.accent,
                marginTop: "4px",
              }}>FOUNDRY</span>
              <div style={{ height: "1px", background: "rgba(255,255,255,0.15)", margin: "6px 0 5px" }} />
              <span style={{
                fontFamily: "'Raleway', sans-serif",
                fontSize: "8px", fontWeight: "300",
                letterSpacing: "3px", color: "rgba(255,255,255,0.4)",
                textTransform: "uppercase",
              }}>Economic Intelligence · Research for the Serious Investor</span>
            </div>
          </div>
          <div style={{ height: "3px", background: `linear-gradient(90deg, ${T.accent} 0%, ${T.accentLt} 50%, transparent 100%)` }} />
        </header>

        {/* SECTION NAV */}
        <nav style={{
          background: T.navy,
          padding: "0 40px",
          display: "flex",
          borderBottom: "2px solid rgba(255,255,255,0.08)",
        }}>
          {["Markets", "Market IQ", "Investing", "Expat Investing ↗"].map((tab, i) => (
            <span key={tab} style={{
              fontFamily: "'Raleway', sans-serif",
              fontSize: "9px", fontWeight: "600",
              letterSpacing: "3px", textTransform: "uppercase",
              color: i === 1 ? T.white : (i === 3 ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.45)"),
              padding: "13px 22px",
              borderBottom: i === 1 ? `2px solid ${T.gold}` : "2px solid transparent",
              marginBottom: "-2px",
              cursor: "pointer",
              fontStyle: i === 3 ? "italic" : "normal",
            }}>{tab}</span>
          ))}
        </nav>

        {/* CONTENT */}
        <div style={{ padding: "36px 40px" }}>

          {/* Section label */}
          <div style={{
            fontFamily: "'Raleway', sans-serif",
            fontSize: "9px", fontWeight: "600",
            letterSpacing: "3px", textTransform: "uppercase",
            color: T.muted, marginBottom: "16px",
          }}>Market IQ — Economic Concepts, Plain & Simple</div>

          {/* Intro blurb */}
          <p style={{
            fontFamily: "'Source Serif 4', serif",
            fontSize: "15px", lineHeight: "1.7",
            color: "#2c2c3e", fontWeight: "300",
            marginBottom: "32px",
            paddingBottom: "24px",
            borderBottom: `1px solid ${T.border}`,
          }}>
            No economics degree required. Each card explains one concept — what it is, why it matters,
            how often it's published, and what the recent trend means for your money.
          </p>

          {/* Category buttons */}
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "32px" }}>
            {["All","Macro Indicators","Inflation","Employment","Central Banks","Markets","Trade & FX"].map((cat, i) => (
              <button key={cat} style={{
                fontFamily: "'Raleway', sans-serif",
                fontSize: "9px", fontWeight: "600",
                letterSpacing: "2px", textTransform: "uppercase",
                padding: "6px 14px",
                border: `1px solid ${i < 2 ? T.navy : T.border}`,
                background: i < 2 ? T.navy : T.white,
                color: i < 2 ? T.white : T.muted,
                cursor: "pointer",
              }}>{cat}</button>
            ))}
          </div>

          {/* ── THE FEATURED FLASHCARD ── */}
          <div style={{ marginBottom: "10px" }}>
            <div style={{
              fontFamily: "'Raleway', sans-serif",
              fontSize: "9px", fontWeight: "600",
              letterSpacing: "3px", textTransform: "uppercase",
              color: T.accent, marginBottom: "14px",
            }}>Featured Card · Macro Indicators</div>

            {/* Card with flip */}
            <div
              style={{
                perspective: "1400px",
                cursor: "pointer",
                width: "100%",
              }}
              onClick={() => setFlipped(f => !f)}
            >
              <div style={{
                position: "relative",
                width: "100%",
                height: "420px",
                transformStyle: "preserve-3d",
                transition: "transform 0.7s cubic-bezier(0.4, 0.2, 0.2, 1)",
                transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
              }}>

                {/* ── FRONT ── */}
                <div style={{
                  position: "absolute", inset: 0,
                  backfaceVisibility: "hidden",
                  WebkitBackfaceVisibility: "hidden",
                  border: `1px solid ${T.border}`,
                  borderTop: `4px solid ${T.accent}`,
                  background: T.offWhite,
                  display: "flex",
                  flexDirection: "column",
                }}>
                  {/* Card header — navy band */}
                  <div style={{
                    background: T.navy,
                    padding: "20px 28px 18px",
                    position: "relative",
                    overflow: "hidden",
                  }}>
                    {/* subtle grid */}
                    <div style={{
                      position: "absolute", inset: 0,
                      backgroundImage: `
                        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
                      `,
                      backgroundSize: "24px 24px",
                    }} />
                    <div style={{ position: "relative" }}>
                      <div style={{
                        fontFamily: "'Raleway', sans-serif",
                        fontSize: "8px", fontWeight: "600",
                        letterSpacing: "2.5px", textTransform: "uppercase",
                        color: T.gold, marginBottom: "8px",
                      }}>Macro Indicators · Card 01</div>
                      <div style={{
                        fontFamily: "'Cormorant Garamond', serif",
                        fontSize: "48px", fontWeight: "600",
                        color: T.white, lineHeight: 1,
                        letterSpacing: "1px",
                      }}>GDP</div>
                      <div style={{
                        fontFamily: "'Source Serif 4', serif",
                        fontSize: "13px", fontWeight: "300",
                        fontStyle: "italic",
                        color: T.accentLt, marginTop: "6px",
                      }}>Gross Domestic Product</div>
                    </div>
                  </div>

                  {/* Card body */}
                  <div style={{ padding: "28px 28px 0", flex: 1 }}>
                    <div style={{
                      fontFamily: "'Raleway', sans-serif",
                      fontSize: "9px", fontWeight: "600",
                      letterSpacing: "2px", textTransform: "uppercase",
                      color: T.muted, marginBottom: "14px",
                    }}>What is it?</div>

                    <p style={{
                      fontFamily: "'Source Serif 4', serif",
                      fontSize: "16px", lineHeight: "1.72",
                      color: T.text, fontWeight: "300",
                      marginBottom: "24px",
                    }}>
                      GDP is the total dollar value of <em>everything</em> a country produces —
                      every good made and every service sold — within a given period.
                      Think of it as the economy's annual report card.
                    </p>

                    <div style={{
                      borderLeft: `3px solid ${T.gold}`,
                      paddingLeft: "16px",
                      marginBottom: "28px",
                    }}>
                      <p style={{
                        fontFamily: "'Source Serif 4', serif",
                        fontSize: "14px", lineHeight: "1.65",
                        color: "#3a3a4a", fontWeight: "300",
                        fontStyle: "italic",
                      }}>
                        GDP = Consumer Spending + Business Investment + Government Spending + (Exports − Imports)
                      </p>
                    </div>

                    <p style={{
                      fontFamily: "'Source Serif 4', serif",
                      fontSize: "14px", lineHeight: "1.65",
                      color: "#3a3a4a", fontWeight: "300",
                    }}>
                      When GDP grows, the economy is expanding — more jobs, rising incomes, stronger profits.
                      When it shrinks for two consecutive quarters, that's the textbook definition
                      of a <strong style={{ color: T.red, fontWeight: "600" }}>recession</strong>.
                    </p>
                  </div>

                  {/* Footer */}
                  <div style={{
                    padding: "18px 28px",
                    borderTop: `1px solid ${T.border}`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}>
                    <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
                      <span style={{
                        fontFamily: "'Raleway', sans-serif",
                        fontSize: "9px", fontWeight: "600",
                        letterSpacing: "1.5px", textTransform: "uppercase",
                        color: T.muted,
                      }}>Published: Quarterly</span>
                      <TrendBadge direction="down" label="Slowing" />
                    </div>
                    <span style={{
                      fontFamily: "'Raleway', sans-serif",
                      fontSize: "9px", fontWeight: "500",
                      letterSpacing: "1.5px", textTransform: "uppercase",
                      color: T.accent,
                    }}>Flip for latest data →</span>
                  </div>
                </div>

                {/* ── BACK ── */}
                <div style={{
                  position: "absolute", inset: 0,
                  backfaceVisibility: "hidden",
                  WebkitBackfaceVisibility: "hidden",
                  transform: "rotateY(180deg)",
                  border: `1px solid ${T.border}`,
                  borderTop: `4px solid ${T.gold}`,
                  background: T.offWhite,
                  display: "flex",
                  flexDirection: "column",
                }}>
                  {/* Back header */}
                  <div style={{
                    background: T.navyMid,
                    padding: "16px 28px",
                    position: "relative", overflow: "hidden",
                  }}>
                    <div style={{
                      position: "absolute", inset: 0,
                      backgroundImage: `
                        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
                      `,
                      backgroundSize: "24px 24px",
                    }} />
                    <div style={{ position: "relative", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{
                          fontFamily: "'Raleway', sans-serif",
                          fontSize: "8px", fontWeight: "600",
                          letterSpacing: "2.5px", textTransform: "uppercase",
                          color: T.gold, marginBottom: "4px",
                        }}>Latest Data · BEA</div>
                        <div style={{
                          fontFamily: "'Cormorant Garamond', serif",
                          fontSize: "22px", fontWeight: "600",
                          color: T.white,
                        }}>GDP — Current Trend</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{
                          fontFamily: "'Cormorant Garamond', serif",
                          fontSize: "32px", fontWeight: "300",
                          color: T.red, lineHeight: 1,
                        }}>1.4%</div>
                        <div style={{
                          fontFamily: "'Raleway', sans-serif",
                          fontSize: "8px", fontWeight: "600",
                          letterSpacing: "1.5px", textTransform: "uppercase",
                          color: "rgba(255,255,255,0.4)", marginTop: "2px",
                        }}>Q4 2025 (Annualized)</div>
                      </div>
                    </div>
                  </div>

                  {/* Back body */}
                  <div style={{ padding: "22px 28px", flex: 1, display: "flex", flexDirection: "column", gap: "18px" }}>

                    {/* Chart section */}
                    <div>
                      <div style={{
                        fontFamily: "'Raleway', sans-serif",
                        fontSize: "9px", fontWeight: "600",
                        letterSpacing: "2px", textTransform: "uppercase",
                        color: T.muted, marginBottom: "14px",
                      }}>Real GDP Growth — Annualized Rate</div>
                      <div style={{
                        background: T.navy,
                        padding: "18px 20px 14px",
                        borderRadius: "1px",
                      }}>
                        <MiniBarChart data={GDP_QUARTERS} />
                      </div>
                    </div>

                    {/* Two stat tiles */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                      {[
                        {
                          label: "Full Year 2025",
                          value: "2.2%",
                          sub: "↓ from 2.8% in 2024",
                          valueColor: T.red,
                        },
                        {
                          label: "2026 Forecast",
                          value: "2.5%",
                          sub: "Goldman Sachs est.",
                          valueColor: T.green,
                        },
                      ].map((stat) => (
                        <div key={stat.label} style={{
                          border: `1px solid ${T.border}`,
                          background: T.white,
                          padding: "14px 16px",
                        }}>
                          <div style={{
                            fontFamily: "'Raleway', sans-serif",
                            fontSize: "8px", fontWeight: "600",
                            letterSpacing: "1.5px", textTransform: "uppercase",
                            color: T.muted, marginBottom: "6px",
                          }}>{stat.label}</div>
                          <div style={{
                            fontFamily: "'Cormorant Garamond', serif",
                            fontSize: "30px", fontWeight: "600",
                            color: stat.valueColor, lineHeight: 1,
                          }}>{stat.value}</div>
                          <div style={{
                            fontFamily: "'Raleway', sans-serif",
                            fontSize: "9px", fontWeight: "500",
                            color: T.muted, marginTop: "4px",
                          }}>{stat.sub}</div>
                        </div>
                      ))}
                    </div>

                    {/* Insight callout */}
                    <div style={{
                      borderLeft: `3px solid ${T.gold}`,
                      paddingLeft: "16px",
                      background: T.white,
                      padding: "14px 16px 14px 16px",
                      borderLeft: `3px solid ${T.gold}`,
                      border: `1px solid ${T.border}`,
                      borderLeftWidth: "3px",
                      borderLeftColor: T.gold,
                    }}>
                      <div style={{
                        fontFamily: "'Raleway', sans-serif",
                        fontSize: "8px", fontWeight: "700",
                        letterSpacing: "2px", textTransform: "uppercase",
                        color: T.gold, marginBottom: "8px",
                      }}>What This Means For You</div>
                      <p style={{
                        fontFamily: "'Source Serif 4', serif",
                        fontSize: "13px", lineHeight: "1.65",
                        color: "#3a3a4a", fontWeight: "300",
                        margin: 0,
                      }}>
                        Q4 2025 stumbled to <strong style={{ color: T.red }}>1.4%</strong> — dragged by the federal
                        government shutdown and tariff headwinds. The slowdown is expected to be temporary;
                        economists project a <strong style={{ color: T.green }}>bounce-back</strong> in early 2026
                        as those one-off drags fade and consumer spending stays resilient.
                      </p>
                    </div>
                  </div>

                  {/* Back footer */}
                  <div style={{
                    padding: "14px 28px",
                    borderTop: `1px solid ${T.border}`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}>
                    <span style={{
                      fontFamily: "'Raleway', sans-serif",
                      fontSize: "9px", fontWeight: "600",
                      letterSpacing: "1.5px", textTransform: "uppercase",
                      color: T.muted,
                    }}>Source: U.S. Bureau of Economic Analysis · Feb 2026</span>
                    <span style={{
                      fontFamily: "'Raleway', sans-serif",
                      fontSize: "9px", fontWeight: "500",
                      letterSpacing: "1.5px", textTransform: "uppercase",
                      color: T.accent,
                    }}>← Flip back</span>
                  </div>
                </div>

              </div>
            </div>
          </div>

          {/* Other sample cards in grid (static, to show context) */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "16px",
            marginTop: "24px",
            opacity: 0.55,
          }}>
            {[
              { cat: "Inflation", term: "CPI", freq: "Monthly", dir: "up", label: "Elevated" },
              { cat: "Central Banks", term: "Fed Funds Rate", freq: "8× per year", dir: "flat", label: "Hold" },
              { cat: "Inflation", term: "PCE", freq: "Monthly", dir: "up", label: "Above Target" },
            ].map(c => (
              <div key={c.term} style={{
                border: `1px solid ${T.border}`,
                borderTop: `4px solid ${T.accent}`,
                background: T.offWhite,
              }}>
                <div style={{ background: T.navy, padding: "12px 14px 10px" }}>
                  <div style={{
                    fontFamily: "'Raleway', sans-serif",
                    fontSize: "8px", fontWeight: "600",
                    letterSpacing: "2.5px", textTransform: "uppercase",
                    color: T.gold, marginBottom: "4px",
                  }}>{c.cat}</div>
                  <div style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: "18px", fontWeight: "600",
                    color: T.white,
                  }}>{c.term}</div>
                </div>
                <div style={{ padding: "12px 14px" }}>
                  <div style={{
                    fontFamily: "'Raleway', sans-serif",
                    fontSize: "9px", fontWeight: "600",
                    letterSpacing: "1.5px", textTransform: "uppercase",
                    color: T.muted,
                  }}>{c.freq}</div>
                </div>
              </div>
            ))}
          </div>

          {/* See all */}
          <div style={{
            textAlign: "center", paddingTop: "24px",
            fontFamily: "'Raleway', sans-serif",
            fontSize: "10px", fontWeight: "600",
            letterSpacing: "2px", textTransform: "uppercase",
          }}>
            <a href="#" style={{ color: T.accent, textDecoration: "none", borderBottom: `1px solid ${T.accent}`, paddingBottom: "2px" }}>
              View all concepts →
            </a>
          </div>

        </div>

        {/* FOOTER */}
        <footer style={{
          background: T.navy,
          padding: "16px 40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <div style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: "14px", fontWeight: "600",
            letterSpacing: "3px", color: "rgba(255,255,255,0.5)",
          }}>FRAMEWORK <span style={{ color: T.accent }}>FOUNDRY</span></div>
          <div style={{
            fontFamily: "'Raleway', sans-serif",
            fontSize: "8.5px", color: "rgba(255,255,255,0.3)",
            letterSpacing: "0.5px", textAlign: "right", lineHeight: "1.6",
          }}>
            For informational purposes only. Not investment advice.<br/>
            Past performance is not indicative of future results.
          </div>
        </footer>
      </div>
    </div>
  );
}
