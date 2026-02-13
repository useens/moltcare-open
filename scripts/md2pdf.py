#!/usr/bin/env python3
"""
Markdown to PDF converter using FPDF
"""

from fpdf import FPDF
from pathlib import Path
import re

class MarkdownPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", size=12)
    
    def header(self):
        self.set_font("Arial", 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "森森 - 超进化模式 v3.0 Singularity", 0, 0, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')
    
    def add_title(self, text, level=1):
        sizes = {1: 20, 2: 16, 3: 14, 4: 12}
        self.set_font("Arial", 'B', sizes.get(level, 12))
        self.set_text_color(0, 0, 0)
        self.ln(5)
        self.multi_cell(0, 10, text)
        self.ln(2)
    
    def add_text(self, text, bold=False, italic=False):
        style = ''
        if bold:
            style += 'B'
        if italic:
            style += 'I'
        self.set_font("Arial", style, 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(2)
    
    def add_code_block(self, text):
        self.set_font("Courier", '', 9)
        self.set_fill_color(240, 240, 240)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(2)
    
    def add_table_row(self, cells, is_header=False):
        if is_header:
            self.set_font("Arial", 'B', 10)
            self.set_fill_color(200, 200, 200)
        else:
            self.set_font("Arial", '', 10)
            self.set_fill_color(255, 255, 255)
        
        col_width = 45
        for cell in cells:
            self.cell(col_width, 8, str(cell)[:20], 1, 0, 'L', is_header)
        self.ln()

def convert_md_to_pdf(md_file, pdf_file):
    """Convert markdown to PDF"""
    pdf = MarkdownPDF()
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple markdown parsing
    lines = content.split('\n')
    in_code_block = False
    code_content = []
    
    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                # End of code block
                pdf.add_code_block('\n'.join(code_content))
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_content.append(line)
            continue
        
        # Headers
        if line.startswith('# '):
            pdf.add_title(line[2:], 1)
        elif line.startswith('## '):
            pdf.add_title(line[3:], 2)
        elif line.startswith('### '):
            pdf.add_title(line[4:], 3)
        elif line.startswith('#### '):
            pdf.add_title(line[5:], 4)
        # Horizontal rule
        elif line.startswith('---'):
            pdf.ln(5)
        # Empty line
        elif not line.strip():
            pdf.ln(2)
        # Regular text
        else:
            # Remove markdown formatting
            text = line
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
            text = re.sub(r'`(.*?)`', r'\1', text)        # Code
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
            
            # Check for bold/italic
            is_bold = line.startswith('**') and line.endswith('**')
            is_italic = line.startswith('*') and line.endswith('*') and not is_bold
            
            if text.strip():
                pdf.add_text(text, bold=is_bold, italic=is_italic)
    
    pdf.output(pdf_file)
    print(f"✅ PDF generated: {pdf_file}")

if __name__ == "__main__":
    import sys
    md_file = sys.argv[1] if len(sys.argv) > 1 else "docs/hyper-evolution-v3-intro.md"
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else "docs/hyper-evolution-v3-intro.pdf"
    
    convert_md_to_pdf(md_file, pdf_file)
