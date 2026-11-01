import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "AutoHeal_Documentation")
SCREENSHOTS_DIR = os.path.join(DOCS_DIR, "screenshots")
DIAGRAMS_DIR = os.path.join(DOCS_DIR, "diagrams")
LOGO_PATH = os.path.join(DOCS_DIR, "university_logo.png")

OUTPUT_DOCX = os.path.join(DOCS_DIR, "AutoHeal_Academic_Project_Report.docx")

def set_cell_background(cell, fill_hex):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal padding for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level=1, space_before=12, space_after=6, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.bold = True
    
    if level == 1:
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0, 32, 96) # Dark Navy
    elif level == 2:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(31, 78, 120)
    elif level == 3:
        run.font.size = Pt(12.5)
        run.font.color.rgb = RGBColor(46, 117, 182)
    else:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(38, 38, 38)
    return p

def add_body_paragraph(doc, text, bold_prefix="", space_after=6, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(12)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(0, 0, 0)
        
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(30, 30, 30)
    return p

def add_bullet_point(doc, text, bold_title=""):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_title:
        r_title = p.add_run(bold_title)
        r_title.font.name = 'Times New Roman'
        r_title.font.size = Pt(12)
        r_title.bold = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    return p

def add_code_snippet(doc, code_str, title=""):
    if title:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(8)
        p_t.paragraph_format.space_after = Pt(2)
        p_t.paragraph_format.keep_with_next = True
        r_t = p_t.add_run(title)
        r_t.font.name = 'Courier New'
        r_t.font.size = Pt(10)
        r_t.bold = True
        r_t.font.color.rgb = RGBColor(31, 78, 120)

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_str)
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(15, 23, 42)
    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_after = Pt(6)

def add_figure_image(doc, img_path, fig_number, caption, explanation="", width_in=6.0):
    if not os.path.exists(img_path):
        print(f"Warning: image path does not exist: {img_path}")
        return
        
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(10)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.keep_with_next = True
    
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=Inches(width_in))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.keep_with_next = True
    
    r_cap_lbl = p_cap.add_run(f"Figure {fig_number}: ")
    r_cap_lbl.font.name = 'Times New Roman'
    r_cap_lbl.font.size = Pt(11)
    r_cap_lbl.bold = True
    r_cap_lbl.font.color.rgb = RGBColor(0, 32, 96)
    
    r_cap_txt = p_cap.add_run(caption)
    r_cap_txt.font.name = 'Times New Roman'
    r_cap_txt.font.size = Pt(11)
    r_cap_txt.bold = True
    
    if explanation:
        p_exp = doc.add_paragraph()
        p_exp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_exp.paragraph_format.space_after = Pt(10)
        r_exp = p_exp.add_run(explanation)
        r_exp.font.name = 'Times New Roman'
        r_exp.font.size = Pt(10.5)
        r_exp.font.italic = True
        r_exp.font.color.rgb = RGBColor(70, 70, 70)

print("Report generator framework verified.")
