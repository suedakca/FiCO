import os
from fpdf import FPDF
import re

class FiCOReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'FiCO v3.2 Engineering Report', border=False, align='C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

def generate_pdf(md_path, pdf_path):
    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found.")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Tam güvenlik için tüm non-ascii ve emojileri temizle
    content = content.encode('ascii', 'ignore').decode('ascii') 

    pdf = FiCOReportPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Basit Fonta Dön
    font_name = "helvetica"
    pdf.set_font(font_name, size=11)
    
    clean_content = re.sub(r'```mermaid.*?```', '[Architecture Diagram]', content, flags=re.DOTALL)
    
    lines = clean_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
            
        if line.startswith('# '):
            pdf.set_font(font_name, 'B', 16)
            pdf.multi_cell(190, 10, line[2:])
        elif line.startswith('## '):
            pdf.set_font(font_name, 'B', 14)
            pdf.multi_cell(190, 9, line[3:])
        elif line.startswith('### '):
            pdf.set_font(font_name, 'B', 12)
            pdf.multi_cell(190, 8, line[4:])
        elif line.startswith('- ') or line.startswith('* '):
            pdf.set_font(font_name, '', 11)
            pdf.multi_cell(190, 7, f"  . {line[2:]}")
        else:
            pdf.set_font(font_name, '', 11)
            pdf.multi_cell(190, 7, line)

    pdf.output(pdf_path)
    print(f"✅ PDF başarıyla oluşturuldu: {pdf_path}")

if __name__ == "__main__":
    MD_FILE = "/Users/suedaakca/.gemini/antigravity/brain/aba7a11c-a3a6-4de9-9477-88e04f5b5025/walkthrough.md"
    PDF_FILE = "/Users/suedaakca/Documents/GitHub/FiCO/FiCO_v32_Engineering_Report.pdf"
    generate_pdf(MD_FILE, PDF_FILE)
