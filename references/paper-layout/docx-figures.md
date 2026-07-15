# DOCX figure contract

- Compute usable width from page width minus left and right margins.
- A4 with conventional margins normally permits about 15.9 cm; use 13.5--15.0 cm for wide figures and less for compact figures.
- Lock aspect ratio. Cap image height at 72% of usable page height and at 20 cm.
- Never copy raw pixel or physical dimensions directly into Word.
- Export through `python 工具/docx_export.py --workspace .`; retain `论文/docx_report.json`.
- The report must show every image width within `usable_width_cm` and every image height within the configured maximum.
- A contest with a hard page limit additionally requires a LibreOffice-generated PDF preview and readable page count.
