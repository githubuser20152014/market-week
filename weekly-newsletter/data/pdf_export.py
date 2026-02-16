"""Export the newsletter as a professionally formatted PDF."""

from fpdf import FPDF
from pathlib import Path


class NewsletterPDF(FPDF):
    """Custom PDF class with Framework Foundry branding."""

    NAVY = (20, 40, 80)
    DARK = (30, 30, 30)
    GRAY = (100, 100, 100)
    LIGHT_BG = (245, 247, 250)
    WHITE = (255, 255, 255)
    GREEN = (34, 139, 34)
    RED = (180, 30, 30)
    ACCENT = (50, 100, 180)

    def header(self):
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 28, "F")
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*self.WHITE)
        self.set_y(6)
        self.cell(0, 10, "Framework Foundry Weekly", ln=True, align="C")
        self.set_font("Helvetica", "I", 11)
        self.cell(0, 7, "Research for the serious investor", ln=True, align="C")
        self.ln(2)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, self._subtitle, ln=True, align="C")
        self.set_y(36)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10,
                  "Disclaimer: For informational purposes only. "
                  "Not investment advice. Past performance is not indicative of future results.",
                  align="C")

    def section_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.NAVY)
        self.cell(0, 8, title, ln=True)
        # Accent underline
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.6)
        x = self.get_x()
        y = self.get_y()
        self.line(x, y, x + 55, y)
        self.ln(4)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.DARK)
        self.multi_cell(0, 5, text)
        self.ln(2)


def generate_pdf(context, chart_path, output_dir, date_str):
    """Generate a PDF newsletter.

    Args:
        context: Template context dict from build_template_context.
        chart_path: Path to the chart PNG.
        output_dir: Directory to save the PDF.
        date_str: Newsletter date string.

    Returns:
        Path to the saved PDF.
    """
    pdf = NewsletterPDF()
    pdf._subtitle = f"Week ending {date_str}"
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # -- The Week in Brief --
    pdf.section_title("The Week in Brief")
    for para in context["narrative"].split("\n\n"):
        pdf.body_text(para.strip())

    # -- Chart --
    if chart_path and Path(chart_path).exists():
        pdf.ln(2)
        chart_w = 180
        pdf.image(str(chart_path), x=15, w=chart_w)
        pdf.ln(4)

    # -- Market Snapshot Table --
    pdf.section_title("Market Snapshot")
    indices = context["indices"]

    col_widths = [38, 30, 25, 50]
    headers = ["Index", "Close", "Weekly %", "Week Range"]

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*pdf.NAVY)
    pdf.set_text_color(*pdf.WHITE)
    for i, h in enumerate(headers):
        align = "L" if i == 0 else "R"
        pdf.cell(col_widths[i], 7, h, border=0, fill=True, align=align)
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    for row_idx, idx in enumerate(indices):
        bg = pdf.LIGHT_BG if row_idx % 2 == 0 else pdf.WHITE
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*pdf.DARK)

        pdf.cell(col_widths[0], 6, idx["name"], border=0, fill=True)

        pdf.cell(col_widths[1], 6, f"{idx['close']:,.2f}", border=0, fill=True, align="R")

        pct = idx["weekly_pct"]
        color = pdf.GREEN if pct >= 0 else pdf.RED
        pdf.set_text_color(*color)
        pdf.cell(col_widths[2], 6, f"{pct:+.2f}%", border=0, fill=True, align="R")

        pdf.set_text_color(*pdf.DARK)
        range_str = f"{idx['week_low']:,.2f} - {idx['week_high']:,.2f}"
        pdf.cell(col_widths[3], 6, range_str, border=0, fill=True, align="R")
        pdf.ln()

    # Best / Worst callout
    best = context.get("best")
    worst = context.get("worst")
    if best and worst:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*pdf.GREEN)
        pdf.cell(90, 5, f"Best: {best['name']} ({best['weekly_pct']:+.2f}%)")
        pdf.set_text_color(*pdf.RED)
        pdf.cell(90, 5, f"Worst: {worst['name']} ({worst['weekly_pct']:+.2f}%)", align="R")
        pdf.ln()

    # -- Economic Events Table --
    pdf.section_title("Last Week's Economic Events")

    econ_cols = [22, 52, 20, 20, 20, 46]  # Date, Event, Actual, Expected, Previous, Surprise
    econ_headers = ["Date", "Event", "Actual", "Expected", "Previous", "Surprise"]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*pdf.NAVY)
    pdf.set_text_color(*pdf.WHITE)
    for i, h in enumerate(econ_headers):
        pdf.cell(econ_cols[i], 7, h, border=0, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for row_idx, ev in enumerate(context.get("past_events", [])):
        bg = pdf.LIGHT_BG if row_idx % 2 == 0 else pdf.WHITE
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*pdf.DARK)

        actual = f"{ev['actual']}{ev.get('unit', '')}"
        expected = f"{ev['expected']}{ev.get('unit', '')}"
        previous = f"{ev['previous']}{ev.get('unit', '')}"
        surprise = ev.get("surprise", "")

        pdf.cell(econ_cols[0], 6, ev["date"], border=0, fill=True, align="C")
        pdf.cell(econ_cols[1], 6, ev["event"], border=0, fill=True)
        pdf.cell(econ_cols[2], 6, actual, border=0, fill=True, align="C")
        pdf.cell(econ_cols[3], 6, expected, border=0, fill=True, align="C")
        pdf.cell(econ_cols[4], 6, previous, border=0, fill=True, align="C")
        pdf.cell(econ_cols[5], 6, surprise, border=0, fill=True, align="C")
        pdf.ln()

    # Investor impact notes below the table
    pdf.ln(3)
    for ev in context.get("past_events", []):
        impact = ev.get("impact", "")
        if impact:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*pdf.DARK)
            pdf.cell(0, 5, f"{ev['event']}:", ln=True)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*pdf.ACCENT)
            pdf.multi_cell(0, 4, impact)
            pdf.ln(1)

    # -- Upcoming Week --
    pdf.section_title("Upcoming Week")
    col_w = [28, 110, 25]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*pdf.NAVY)
    pdf.set_text_color(*pdf.WHITE)
    for i, h in enumerate(["Date", "Event", "Importance"]):
        pdf.cell(col_w[i], 7, h, border=0, fill=True, align="L" if i < 2 else "C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for row_idx, ev in enumerate(context.get("upcoming_events", [])):
        bg = pdf.LIGHT_BG if row_idx % 2 == 0 else pdf.WHITE
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*pdf.DARK)
        pdf.cell(col_w[0], 6, ev["date"], border=0, fill=True)
        pdf.cell(col_w[1], 6, ev["event"], border=0, fill=True)
        imp = ev.get("importance", 1)
        label = "High" if imp >= 3 else ("Medium" if imp == 2 else "Low")
        pdf.cell(col_w[2], 6, label, border=0, fill=True, align="C")
        pdf.ln()

    # -- Positioning Tips Table --
    pdf.section_title("Positioning Tips")

    sig_w = 70
    act_w = 110
    line_h = 4.5
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*pdf.NAVY)
    pdf.set_text_color(*pdf.WHITE)
    pdf.cell(sig_w, 7, "Signal", border=0, fill=True)
    pdf.cell(act_w, 7, "Action", border=0, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for row_idx, tip in enumerate(context.get("tips", [])):
        bg = pdf.LIGHT_BG if row_idx % 2 == 0 else pdf.WHITE

        # Split on " -- " to get signal and action
        if " -- " in tip:
            signal, action = tip.split(" -- ", 1)
        else:
            signal, action = tip, ""

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        # Measure both columns by rendering off-screen
        pdf.set_font("Helvetica", "", 8)
        sig_lines = pdf.multi_cell(sig_w, line_h, signal, border=0, split_only=True)
        act_lines = pdf.multi_cell(act_w, line_h, action, border=0, split_only=True)
        row_h = max(len(sig_lines), len(act_lines)) * line_h

        # Draw background for both columns
        pdf.set_fill_color(*bg)
        pdf.rect(x_start, y_start, sig_w + act_w, row_h, "F")

        # Render signal column
        pdf.set_xy(x_start, y_start)
        pdf.set_text_color(*pdf.DARK)
        pdf.multi_cell(sig_w, line_h, signal, border=0)

        # Render action column
        pdf.set_xy(x_start + sig_w, y_start)
        pdf.set_text_color(*pdf.GRAY)
        pdf.multi_cell(act_w, line_h, action, border=0)

        pdf.set_xy(x_start, y_start + row_h)

    # Save
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    pdf_path = output_dir / f"newsletter_{date_str}.pdf"
    pdf.output(str(pdf_path))
    return pdf_path
