# Documents Plugin Interactive Paper Construction Guide

This document explains how to use the Documents plugin to interactively build mathematical modeling contest papers.
This is a replacement for the old monolithic `build_docx.py` script approach, offering 3-5x speed improvement.

---

## Core Principle: Section-by-Section Construction + Instant Rendering

**Do not write the entire paper before checking.** Instead:

```
Write one section -> Render PNG -> Check effect -> Pass: continue, Fail: fix immediately
```

This avoids the fundamental problem of the old approach: writing 200+ lines of script only to discover formatting errors that require a full rewrite.

---

## Preparation

### 1. Verify Documents Plugin Availability

```python
# Test python-docx availability
from docx import Document
doc = Document()
doc.save("test.docx")
print("OK")
```

### 2. Verify Rendering Chain

```bash
python render_docx.py test.docx --output_dir ./qa/
# Check if qa/page-1.png was generated
```

### 3. Load Competition Template

```python
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document("templates/51mcm_template.docx")
```

The template has predefined page margins, default fonts, and paragraph styles. Just fill in content; formatting inherits from the template.

---

## Phase 1: Title Page + Abstract (Pages 1-2)

### Set Paper Title

```python
title_para = doc.paragraphs[0]  # Assume template first paragraph is title slot
title_para.clear()
title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_para.add_run("Problem C: Research on Mathematical Model for Slope Warning")
run.font.name = "HeiTi"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "HeiTi")
run.font.size = Pt(16)
run.font.bold = True
```

### Set Abstract

```python
# "Abstract" title
abs_title = doc.add_paragraph()
run = abs_title.add_run("Abstract")
run.font.name = "HeiTi"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "HeiTi")
run.font.size = Pt(14)
run.font.bold = True

# Abstract body
abs_body = doc.add_paragraph()
abs_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
abs_body.paragraph_format.first_line_indent = Cm(0.74)
run = abs_body.add_run("This paper addresses the slope warning problem by establishing...")
run.font.name = "SongTi"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "SongTi")
run.font.size = Pt(12)
```

### First Render Check

```bash
python render_docx.py output/paper.docx --output_dir output/qa/
```

Check `qa/page-1.png` and `page-2.png` to confirm:
- Title centered, HeiTi font, size 3
- Abstract title HeiTi size 4
- Abstract body SongTi, small size 4, first-line indent

---

## Phase 2: Problem Restatement + Problem Analysis

```python
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Level 1 heading
h1 = doc.add_paragraph()
h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = h1.add_run("I. Problem Restatement")
run.font.name = "HeiTi"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "HeiTi")
run.font.size = Pt(14)
run.font.bold = True

# Body paragraph (encapsulate as function)
def add_body(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text)
    run.font.name = "SongTi"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "SongTi")
    run.font.size = Pt(12)
    return p

add_body(doc, "Slope stability warning is a key issue in geological disaster prevention...")
```

Render check after each section.

---

## Phase 3: Model Establishment and Solution (Per Sub-Question)

### Sub-Question Structure Template

```
4.x.1 Model Establishment
  P1: Problem positioning (what to solve + why hard)
  P2: Modeling approach (choose method + why)
  P3: Mathematical derivation (complete formulas + variable explanation)
  P4: Method advantages and assumptions

4.x.2 Model Solution and Result Analysis
  P1: Solution process (how to solve + parameter selection basis)
  P2: Core results (numbers + meaning)
  P3: Cross-validation / robustness (indicators + meaning)
  P4: Physical/engineering interpretation

[Insert figure + figure caption]
```

### Insert OMML Formula

```python
from scripts.build_docx import build_omath, _mr, om_sub, om_frac, om_sum

omath = build_omath(
    _mr("F_"), om_sub("s", "safe"), _mr(" = "),
    om_frac(_mr("R"), _mr("S"))
)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run()
run._element.append(omath)
```

### Insert Three-Line Table

```python
from scripts.build_docx import add_three_line_table

table = add_three_line_table(
    doc,
    headers=["Parameter", "Meaning", "Value"],
    rows=[
        ["c", "Cohesion (kPa)", "25.0"],
        ["phi", "Internal friction angle (deg)", "30.0"],
        ["gamma", "Unit weight (kN/m^3)", "18.5"],
    ],
    caption="Table 2: Slope geotechnical parameters"
)
```

### Insert Image

```python
from docx.shared import Inches

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run()
run.add_picture("latex/images/fig1_calibration.png", width=Inches(5.5))

# Figure title
cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = cap.add_run("Figure 1: Slope displacement monitoring data calibration results")
run.font.name = "HeiTi"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "HeiTi")
run.font.size = Pt(10.5)
run.font.bold = True
```

**Every figure/table must have a descriptive caption paragraph** (nature-writing standard).

---

## Phase 4: References + Appendix

```python
# References heading
h1 = doc.add_paragraph()
h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = h1.add_run("References")
run.font.name = "HeiTi"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "HeiTi")
run.font.size = Pt(14)
run.font.bold = True

# Reference entries
refs = [
    "[1] Duncan J M. State of the art: limit equilibrium and finite-element analysis of slopes. Journal of Geotechnical Engineering, 1996, 122(7): 577-596.",
    "[2] Chen Z Y. Soil Slope Stability Analysis -- Principles, Methods, Programs. Beijing: China Water & Power Press, 2003.",
]
for ref in refs:
    p = doc.add_paragraph()
    run = p.add_run(ref)
    run.font.name = "SongTi"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "SongTi")
    run.font.size = Pt(12)
```

---

## Phase 5: Final Render QA

```bash
python render_docx.py output/paper.docx --output_dir output/qa/ --emit_pdf
```

### Page-by-Page Checklist

Check all `output/qa/page-<N>.png` files (100% zoom), page by page:

| Check Item | Standard |
|------------|----------|
| Fonts | Titles HeiTi, body SongTi, numbers Times New Roman |
| Font sizes | Title size 3, level 1 size 4, body small size 4, table size 5 |
| Alignment | Titles centered, body justified, tables centered |
| Three-line tables | Top line 1.5pt, below header 0.5pt, bottom line 1.5pt, no vertical lines |
| Formulas | OMML rendered correctly, centered, numbers right-aligned |
| Images | Clear, no blur; figure title HeiTi size 5 centered |
| Line spacing | Single-spaced, first-line indent 2 characters |
| Page numbers | No headers/footers, page count <= 30 |
| Content complete | All sections in order, no omissions |

### When Issues Are Found

1. Modify the corresponding python-docx code section
2. Re-run rendering
3. Re-check the page PNG
4. Repeat until pass

---

## Final Delivery

```python
doc.save("output/paper-C-xxx.docx")
```

```bash
# Optional: convert to PDF submission format
python render_docx.py output/paper-C-xxx.docx --output_dir output/ --emit_pdf
```

### Pre-Delivery Final Confirmation

- [ ] All page PNG checks passed
- [ ] `quality_gate.py` format check passed
- [ ] Word count meets requirements (abstract <= 1 page, body <= 30 pages)
- [ ] No bare numbers, no orphan figures, no black-box jumps
- [ ] References >= 2 per sub-question
- [ ] AI disclosure in appendix

## Common Issues

### Q: Chinese characters display as boxes?
Set `run._element.rPr.rFonts.set(qn("w:eastAsia"), "SongTi")`.

### Q: Three-line table borders incorrect?
Use the `add_three_line_table()` function from `scripts/build_docx.py`; do not manually set table borders.

### Q: Formulas not rendering?
Ensure you imported `build_omath` and all required helper functions. OMML formulas can only be inserted via `run._element.append(omath)`, not `run.text`.

### Q: Rendered PNG has ghosting?
This is a known issue with LibreOffice headless mode; it does not affect the actual DOCX file. Judge based on the Word display for final decisions.

### Q: Render command errors?
See the Documents plugin's `troubleshooting/libreoffice_headless.md`.
