#!/usr/bin/env python3
from docx import Document

doc = Document("/root/.openclaw/media/inbound/nvdia---dd66181f-dc57-4c6f-9342-89edd79f5263.docx")

print("文档内容:")
print("=" * 50)

for para in doc.paragraphs:
    text = para.text.strip()
    if text:
        print(text)

print()
print("=" * 50)
