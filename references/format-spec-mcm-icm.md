# MCM/ICM Paper Format Specification

Based on COMAP official 2026 contest instructions and the mcmthesis LaTeX template specification.
All DOCX/PDF generation must strictly follow this specification.

## Official Hard Requirements (Must Follow)

### Basic Requirements

| Item | Requirement |
|------|-------------|
| Language | **Must** be written and formatted in **English** |
| File format | Must be submitted as **a single Adobe PDF** file |
| Font | Must use **readable fonts, no smaller than 12pt** |
| Page limit | Entire solution (including all parts) **must not exceed 25 pages** |
| File size | Attachment must be **< 25MB** |
| File naming | Named using team control number, e.g., `0000000.pdf` |

### Header/Footer Standards

- **Every page** must include the **team control number** and **current page number**
- Format example: `Team # 0000000, Page 6 of 25`
- Typically placed in the header or footer

### Summary Sheet

- **The summary sheet is the first page of the solution** and is an essential part
- Use the official template (Word or LaTeX)
- Content: Clearly and concisely describe the team's approach and most important conclusions
- **Do not** simply restate the problem or copy from the introduction
- **Recommended to write the summary last**

### 25-Page Limit (Strict)

The 25-page limit covers **all content**:
- Summary sheet (page 1)
- Table of contents (encouraged, but counts toward page limit)
- Problem restatement/clarification
- Variables and assumptions
- Model design and analysis
- Model testing, error analysis, sensitivity analysis
- Model strengths/weaknesses discussion
- Conclusions and results
- References / bibliography
- Notes pages
- Appendix (optional)
- Code (if applicable)
- Any problem-specific required sections

**Important exception**: The "AI Usage Report" is appended after the solution and **does not count toward the 25-page limit**.

### Anonymity Requirements

- **All pages** of the solution must **not** contain any identifiable information, including student, advisor, or school names
- The only allowed identifier is the **team control number**

### Figures/Tables/Formulas

- Figures/tables may be included in the body
- **Do not** submit separate data files, computer programs, or other files with the solution
- All figures/tables must be cited and discussed in the body

### Reference Standards

- All external source information (including AI tools) must be recorded through **footnotes, endnotes, or in-text citations**
- **Fully listed** in the reference list
- Recommended citation format: APA, IEEE, or ACM standards

### AI Tool Usage Rules (2026 New Changes)

1. **Transparency principle**: Teams must be open and honest about all AI tool usage
2. **In-paper declaration**: In the 25-page solution, clearly indicate via in-text citations and references which AI models were used and for what purpose
3. **AI Usage Report**: After the 25 pages, **must attach a separate "AI Usage Report"**, no page limit
4. **Responsibility**: Teams must verify the accuracy of AI-generated content and ensure no unintentional plagiarism

### Submission Rules

| Item | Requirement |
|------|-------------|
| Submission method | Submit via COMAP's designated online form |
| Number of submissions | **Send only once**, do not resubmit |
| Submission information | Team control number, advisor ID, selected problem code (A-F) |
| Work deadline | Monday, Feb 2, 2026, EST 20:00 |
| Submission deadline | Monday, Feb 2, 2026, EST 21:00 |

---

## Common Typesetting Standards (Recommended Practices)

### Recommended Fonts

| Element | Recommended Font | Size |
|---------|-----------------|------|
| Body text | Times New Roman | 12pt |
| Heading 1 | Times New Roman Bold | 14-16pt |
| Heading 2 | Times New Roman Bold | 12-14pt |
| Summary | Times New Roman | 12pt |
| Figure/table titles | Times New Roman | 10-12pt |
| Footnotes/endnotes | Times New Roman | 10pt |
| Code | Courier New or Consolas | 10-11pt |

### Recommended Page Setup

| Item | Recommended Value |
|------|------------------|
| Paper | Letter (8.5" x 11") or A4 |
| Margins | 1 inch (2.54 cm) all sides |
| Line spacing | 1.15 - 1.5x |
| Paragraph spacing | 6pt after paragraph |

### Paper Structure (Recommended)

| Section | Content | Notes |
|---------|---------|-------|
| Page 1 | **Summary Sheet** | Official template, method + key conclusions |
| Pages 2-3 | Table of Contents + Introduction | Problem restatement and analysis |
| Pages 3-5 | Assumptions & Justifications | Assumption list with rationale |
| Pages 5-15 | Model Development | Model construction, derivation, solution |
| Pages 15-20 | Results & Analysis | Results display, sensitivity analysis, error analysis |
| Pages 20-22 | Model Evaluation | Strengths/weaknesses discussion, model validation |
| Pages 22-23 | Conclusions | Conclusions and recommendations |
| Pages 23-24 | References | Reference list |
| Pages 24-25 | Appendices | Appendix (code, additional figures, etc.) |
| After page 25 | **AI Usage Report** | Not counted in page limit |

### Figure/Table/Formula Standards

- Tables: three-line table recommended, top/bottom lines 1-1.5pt, below header 0.5pt, no vertical lines, header bold
- English numbering: Table 1, Table 2, ... / Fig. 1, Fig. 2, ...
- Formulas: LaTeX math environment or Word equation editor; centered, number right-aligned
- Variables: italic; constants/function names: upright
- In-text: Eq. (1), Eq. (2), ...
- Figures: resolution >= 300 DPI, title below figure, axis labels with units, legend complete

### Reference Format (IEEE Recommended)

Journal: [1] A. Author, B. Author, and C. Author, "Title of paper," Journal Name, vol. X, no. Y, pp. XX-XX, Month Year.
Book: [2] A. Author, Title of Book. City, State: Publisher, Year.
Web: [3] A. Author, "Title of page," Website Name, URL, Accessed: Month Day, Year.

---

## Summary Sheet Template

```
SUMMARY
[solution summary in 150-250 words]
Keywords: [keyword1; keyword2; keyword3; keyword4; keyword5]

1. Introduction / Problem Restatement
   [brief problem context]

2. Model Overview
   [model names and selection rationale]

3. Key Results
   [2-3 most important quantitative results]

4. Conclusions
   [main findings and recommendations]
```

## Reviewer Focus Points

1. **Summary Sheet quality**: Concise and powerful summary of methods and core results?
2. **Communication quality**: Is the paper clear, persuasive, and logically coherent?
3. **Model depth**: Is method selection reasonable? Is derivation rigorous?
4. **Result verification**: Are sensitivity analysis, error analysis, and baseline comparison sufficient?
5. **Writing quality**: Language expression, figure/table quality, citation standards?
6. **Innovation**: Method innovation or unique perspective can earn bonus points?
