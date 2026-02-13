#!/usr/bin/env python3
"""
Markdown to PDF converter with Chinese support
Using ReportLab with Noto Sans CJK font
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
from pathlib import Path

# Register Chinese font
pdfmetrics.registerFont(TTFont('SimHei', '/tmp/SimHei.ttf'))

def markdown_to_pdf(md_file, pdf_file):
    """Convert markdown to PDF with Chinese support"""
    
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles with Chinese font
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='SimHei',
        fontSize=24,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontName='SimHei',
        fontSize=18,
        textColor=colors.HexColor('#16213e'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName='SimHei',
        fontSize=14,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontName='SimHei',
        fontSize=12,
        textColor=colors.HexColor('#533483'),
        spaceAfter=8,
        spaceBefore=8
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='SimHei',
        fontSize=10,
        leading=14,
        spaceAfter=6
    )
    
    quote_style = ParagraphStyle(
        'CustomQuote',
        parent=styles['BodyText'],
        fontName='SimHei',
        fontSize=10,
        leftIndent=20,
        textColor=colors.HexColor('#666666'),
        fontStyle='italic'
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph("🌌 超进化模式 v3.0 - Singularity (奇点)", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip the main title (already added)
        if line.startswith('# 🌌 超进化模式'):
            i += 1
            continue
        
        # Horizontal rule
        if line.startswith('---'):
            story.append(Spacer(1, 0.3*cm))
            i += 1
            continue
        
        # Header 1
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, h1_style))
            i += 1
            continue
        
        # Header 2
        if line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, h2_style))
            i += 1
            continue
        
        # Header 3
        if line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, h3_style))
            i += 1
            continue
        
        # Quote
        if line.startswith('> '):
            text = line[2:].strip()
            story.append(Paragraph(text, quote_style))
            i += 1
            continue
        
        # Table
        if line.startswith('|') and i + 1 < len(lines) and '---' in lines[i+1]:
            # Parse table
            table_data = []
            while i < len(lines) and lines[i].startswith('|'):
                row = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                table_data.append(row)
                i += 1
            
            if table_data:
                # Create table (skip header separator)
                data_rows = [table_data[0]] + table_data[2:] if len(table_data) > 2 else table_data
                
                if data_rows:
                    table = Table(data_rows, colWidths=[4*cm, 3*cm, 4*cm, 2.5*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'SimHei'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'SimHei'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.3*cm))
            continue
        
        # Code block
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # Skip closing ```
            
            if code_lines:
                code_text = '<pre>' + '\n'.join(code_lines) + '</pre>'
                story.append(Paragraph(code_text, body_style))
                story.append(Spacer(1, 0.2*cm))
            continue
        
        # Empty line
        if not line.strip():
            story.append(Spacer(1, 0.2*cm))
            i += 1
            continue
        
        # Regular text with markdown formatting
        text = line
        # Convert markdown bold/italic to HTML-like tags
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        # Escape special characters for ReportLab
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Restore HTML tags
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        text = text.replace('&lt;code&gt;', '<code>').replace('&lt;/code&gt;', '</code>')
        text = text.replace('&lt;pre&gt;', '<pre>').replace('&lt;/pre&gt;', '</pre>')
        
        if text.strip():
            story.append(Paragraph(text, body_style))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f"✅ PDF生成成功: {pdf_file}")

if __name__ == "__main__":
    import sys
    md_file = sys.argv[1] if len(sys.argv) > 1 else "docs/hyper-evolution-v3-intro.md"
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else "docs/hyper-evolution-v3-intro.pdf"
    
    markdown_to_pdf(md_file, pdf_file)
