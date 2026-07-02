import pandas as pd
from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. Initialize Faker and generate fake data
fake = Faker('en_IN')
data = []

for _ in range(10): # Adjust this number to generate more rows
    data.append({
        "Name": fake.name(),
        "Email": fake.ascii_free_email(),
        "SSN": fake.ssn(),
        "DOB": fake.date_of_birth(minimum_age=18, maximum_age=75).strftime('%Y-%m-%d'),
        "Credit Card": fake.credit_card_number(card_type='visa'),
        "Phone": fake.phone_number()
    })

# Convert the list of dicts to a pandas DataFrame
df = pd.DataFrame(data)

# =========================================================================
# FILE 1: Export to CSV
# =========================================================================
df.to_csv('sensitive_data.csv', index=False)
print("Successfully generated: sensitive_data.csv")

# =========================================================================
# FILE 2: Export to TXT (Tab-Delimited text formatting)
# =========================================================================
df.to_csv('sensitive_data.txt', sep='\t', index=False)
print("Successfully generated: sensitive_data.txt")

# =========================================================================
# FILE 3: Export to PDF (Nicely formatted clean table)
# =========================================================================
pdf_filename = "sensitive_data.pdf"
doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
story = []

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'TitleStyle',
    parent=styles['Heading1'],
    fontSize=16,
    spaceAfter=15,
    textColor=colors.HexColor('#1A365D')
)
cell_style = ParagraphStyle('CellStyle', fontSize=8, leading=10)
header_style = ParagraphStyle('HeaderStyle', fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=colors.white)

# Title
story.append(Paragraph("Synthetic Sensitive Personal Data Sample File", title_style))
story.append(Spacer(1, 10))

# Convert DataFrame table to list elements wrapped in Paragraph objects (avoids truncation)
table_data = []
# Headers
headers = [Paragraph(col, header_style) for col in df.columns]
table_data.append(headers)

# Rows
for index, row in df.iterrows():
    row_cells = [Paragraph(str(item), cell_style) for item in row]
    table_data.append(row_cells)

# Define column widths to prevent page clipping
col_widths = [80, 110, 70, 60, 110, 110]
pdf_table = Table(table_data, colWidths=col_widths)

# Table Styling
style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('TOPPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ('TOPPADDING', (0, 1), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
])
pdf_table.setStyle(style)
story.append(pdf_table)

# Build PDF
doc.build(story)
print("Successfully generated: sensitive_data.pdf")