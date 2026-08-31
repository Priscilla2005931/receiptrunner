from collections import defaultdict
from datetime import date, datetime
from google import genai
from google.cloud import firestore
from config import PROJECT_ID, LOCATION, GEMINI_MODEL
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import os
from datetime import datetime
from google.genai import types

def render_pdf(report_data: dict, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    month_label = f"{report_data['year']}-{report_data['month']:02d}"
    timestamp = datetime.now().strftime("%H%M%S")
    output_path = os.path.join(output_dir, f"report_{month_label}_{timestamp}.pdf")
    ...

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1F3864")
)
BODY_STYLE = styles["BodyText"]
INSIGHTS_STYLE = ParagraphStyle(
    "InsightsStyle", parent=styles["BodyText"], leftIndent=8, spaceBefore=4
)


def render_pdf(report_data: dict, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    month_label = f"{report_data['year']}-{report_data['month']:02d}"
    output_path = os.path.join(output_dir, f"report_{month_label}.pdf")

    sorted_categories = sorted(report_data["by_category"].items(), key=lambda x: -x[1])

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    elements = []

    # Title
    elements.append(Paragraph(f"ReceiptRunner Monthly Report — {month_label}", TITLE_STYLE))
    elements.append(Spacer(1, 0.15 * inch))

    # Summary box
    summary_text = (
        f"<b>Total Spend:</b> Rs {report_data['total']:.2f}<br/>"
        f"<b>Transactions:</b> {report_data['count']}"
    )
    summary_table = Table([[Paragraph(summary_text, BODY_STYLE)]], colWidths=[6.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f2f2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Category table
    table_data = [["Category", "Amount (Rs)"]]
    for cat, amt in sorted_categories:
        table_data.append([cat, f"{amt:.2f}"])

    cat_table = Table(table_data, colWidths=[3.5 * inch, 3 * inch])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Insights box
    insights_table = Table(
        [[Paragraph(f"<b>Insights:</b><br/>{report_data['insights']}", INSIGHTS_STYLE)]],
        colWidths=[6.5 * inch]
    )
    insights_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4ff")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#1F3864")),
    ]))
    elements.append(insights_table)

    doc.build(elements)
    print(f"\n✓ PDF report saved to: {output_path}")
    return output_path


db = firestore.Client()
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def get_month_expenses(year: int, month: int):
    start = f"{year}-{month:02d}-01"
    end_month = month + 1 if month < 12 else 1
    end_year = year if month < 12 else year + 1
    end = f"{end_year}-{end_month:02d}-01"

    docs = db.collection("expenses") \
        .where("status", "==", "processed") \
        .where("date", ">=", start) \
        .where("date", "<", end) \
        .stream()

    return [d.to_dict() for d in docs]

def aggregate_by_category(expenses):
    by_category = defaultdict(float)
    for e in expenses:
        category = e.get("category", "Other") or "Other"
        amount = e.get("amount", 0) or 0
        by_category[category] += amount
    return dict(by_category)


def generate_insights(by_category: dict, total: float, count: int) -> str:
    prompt = f"""
    Here is a month's expense breakdown by category (all amounts in Indian Rupees, Rs): {by_category}
    Total spend: Rs {total}, Number of transactions: {count}

    Write a concise 3-4 sentence summary highlighting the top spending
    category, any notable concentration of spend, and one practical
    observation. Use "Rs" for currency, not "$". Be matter-of-fact, no fluff.
    """
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt]
    )
    return response.text


def build_report(year: int, month: int):
    expenses = get_month_expenses(year, month)

    if not expenses:
        print(f"No expenses found for {year}-{month:02d}")
        return None

    by_category = aggregate_by_category(expenses)
    total = sum(by_category.values())
    insights = generate_insights(by_category, total, len(expenses))

    print(f"\n=== Expense Report: {year}-{month:02d} ===")
    print(f"Total transactions: {len(expenses)}")
    print(f"Total spend: Rs {total:.2f}\n")
    print("By category:")
    for cat, amt in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: Rs {amt:.2f}")
    print(f"\nInsights:\n{insights}")

    return {
        "year": year,
        "month": month,
        "total": total,
        "count": len(expenses),
        "by_category": by_category,
        "insights": insights,
        "expenses": expenses,
    }


if __name__ == "__main__":
    report_data = build_report(2026, 7)
    if report_data:
        render_pdf(report_data)