"""
reports.py
-----------
Generates PDF and CSV reports for the Student Management System --
covers the "Generate reports" objective.
"""

import csv
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


STUDENT_COLUMNS = [
    ("roll", "Student ID"),
    ("name", "Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("status", "Status"),
]

COURSE_COLUMNS = [
    ("course_name", "Course Name"),
    ("course_code", "Code"),
    ("duration", "Duration"),
    ("fee", "Fee"),
    ("status", "Status"),
]


def _student_rows(students):
    rows = []
    for s in students:
        rows.append({
            "roll": f"#STU{s['id']:03d}",
            "name": f"{s['first_name']} {s['last_name']}",
            "email": s["email"],
            "phone": s["phone"] or "-",
            "status": "Active" if s["is_active"] else "Inactive",
        })
    return rows


def _course_rows(courses):
    rows = []
    for c in courses:
        rows.append({
            "course_name": c["course_name"],
            "course_code": c["course_code"],
            "duration": c["duration"] or "-",
            "fee": f"Rs.{c['fee']:.2f}",
            "status": "Active" if c["is_active"] else "Inactive",
        })
    return rows


def generate_csv(items, kind="students"):
    columns = STUDENT_COLUMNS if kind == "students" else COURSE_COLUMNS
    rows = _student_rows(items) if kind == "students" else _course_rows(items)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([label for _, label in columns])
    for row in rows:
        writer.writerow([row[key] for key, _ in columns])

    byte_output = io.BytesIO()
    byte_output.write(output.getvalue().encode("utf-8"))
    byte_output.seek(0)
    return byte_output


def generate_pdf(items, kind="students", title="Report"):
    columns = STUDENT_COLUMNS if kind == "students" else COURSE_COLUMNS
    rows = _student_rows(items) if kind == "students" else _course_rows(items)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=18 * mm,
        bottomMargin=15 * mm,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, spaceAfter=4)
    subtitle_style = ParagraphStyle("SubtitleStyle", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    elements = [
        Paragraph(title, title_style),
        Paragraph(
            f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')} "
            f"&nbsp;|&nbsp; Total records: {len(rows)}",
            subtitle_style,
        ),
        Spacer(1, 10),
    ]

    header = [label for _, label in columns]
    data = [header]
    for row in rows:
        data.append([row[key] for key, _ in columns])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
