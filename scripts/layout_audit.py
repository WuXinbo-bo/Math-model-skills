from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _rect_area(rect: tuple[float, float, float, float]) -> float:
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def audit_pdf(pdf_path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {"available": False, "pages": [], "issues": [], "warnings": []}
    try:
        import fitz  # type: ignore
    except ImportError:
        report["warnings"].append("PyMuPDF is unavailable; rendered page composition was not audited")
        return report
    if not pdf_path.exists():
        report["issues"].append(f"PDF does not exist: {pdf_path}")
        return report
    report["available"] = True
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        report["warnings"].append(f"PDF page composition could not be opened by PyMuPDF: {exc}")
        return report
    low_density_pages: list[int] = []
    for index, page in enumerate(document):
        width, height = float(page.rect.width), float(page.rect.height)
        blocks = page.get_text("dict").get("blocks", [])
        boxes: list[tuple[float, float, float, float]] = []
        text_blocks: list[tuple[float, str]] = []
        image_area = 0.0
        text_chars = 0
        font_sizes: list[float] = []
        small_text_chars = 0
        clipped = False
        for block in blocks:
            bbox = tuple(float(value) for value in block.get("bbox", (0, 0, 0, 0)))
            if len(bbox) != 4:
                continue
            if bbox[0] < -0.5 or bbox[1] < -0.5 or bbox[2] > width + 0.5 or bbox[3] > height + 0.5:
                clipped = True
            if block.get("type") == 1:
                boxes.append(bbox)  # type: ignore[arg-type]
                image_area += _rect_area(bbox)  # type: ignore[arg-type]
                continue
            lines = block.get("lines", [])
            block_text = "".join(span.get("text", "") for line in lines for span in line.get("spans", []))
            is_page_number = bbox[1] > height * 0.90 and bool(re.fullmatch(r"\s*[-—]?\s*\d+\s*[-—]?\s*", block_text))
            if not is_page_number:
                boxes.append(bbox)  # type: ignore[arg-type]
            text_chars += len(re.sub(r"\s+", "", block_text))
            if block_text.strip() and not is_page_number:
                text_blocks.append((bbox[1], block_text.strip()))
            for line in lines:
                for span in line.get("spans", []):
                    size = float(span.get("size") or 0)
                    chars = len(re.sub(r"\s+", "", str(span.get("text") or "")))
                    if size > 0:
                        font_sizes.append(size)
                    if size < 7.0:
                        small_text_chars += chars
        page_number = index + 1
        if boxes:
            x0 = min(box[0] for box in boxes)
            y0 = min(box[1] for box in boxes)
            x1 = max(box[2] for box in boxes)
            y1 = max(box[3] for box in boxes)
            used_height_ratio = max(0.0, min(1.0, (y1 - y0) / height))
            bottom_whitespace_ratio = max(0.0, min(1.0, (height - y1) / height))
        else:
            used_height_ratio = 0.0
            bottom_whitespace_ratio = 1.0
        image_ratio = min(1.0, image_area / max(1.0, width * height))
        min_font = min(font_sizes) if font_sizes else None
        if clipped:
            report["issues"].append(f"page {page_number}: content extends outside the page box")
        if small_text_chars > max(50, int(text_chars * 0.08)):
            report["issues"].append(f"page {page_number}: {small_text_chars} vector-text characters are smaller than 7pt")
        elif small_text_chars > max(20, int(text_chars * 0.03)):
            report["warnings"].append(f"page {page_number}: review {small_text_chars} vector-text characters smaller than 7pt")
        if 1 < page_number < len(document) and text_chars < 120 and image_ratio < 0.18:
            low_density_pages.append(page_number)
            report["warnings"].append(f"page {page_number}: unusually low information density ({text_chars} text chars)")
        if 1 < page_number < len(document) and used_height_ratio < 0.45:
            report["warnings"].append(f"page {page_number}: content uses only {used_height_ratio:.0%} of page height")
        if bottom_whitespace_ratio > 0.34 and text_chars > 120:
            report["warnings"].append(f"page {page_number}: bottom whitespace is {bottom_whitespace_ratio:.0%}")
        if text_blocks:
            last_y, last_text = max(text_blocks, key=lambda item: item[0])
            heading_like = bool(re.match(r"^(?:\d+(?:\.\d+)*\s+\S+|[一二三四五六七八九十]+、\s*\S+)", last_text))
            if heading_like and last_y > height * 0.82 and len(last_text) < 45:
                report["issues"].append(f"page {page_number}: possible orphan heading near page bottom: {last_text[:30]}")
        report["pages"].append({
            "page": page_number,
            "text_chars": text_chars,
            "image_area_ratio": round(image_ratio, 4),
            "used_height_ratio": round(used_height_ratio, 4),
            "bottom_whitespace_ratio": round(bottom_whitespace_ratio, 4),
            "minimum_font_pt": round(min_font, 2) if min_font is not None else None,
        })
    for left, right in zip(low_density_pages, low_density_pages[1:]):
        if right == left + 1:
            report["warnings"].append(f"pages {left}-{right}: consecutive low-density pages require manual review")
    document.close()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit final PDF page composition after LaTeX compilation.")
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    report = audit_pdf(args.pdf.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
