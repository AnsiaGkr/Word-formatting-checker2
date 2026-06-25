from docx import Document
import re

EXPECTED_FONT = "Calibri"
EXPECTED_SIZE = 11

ALLOWED_MATH_FONTS = ["Cambria Math", "Symbol"]
CAPTION_STARTS = ("Figure", "Fig.", "Table")
REFERENCE_HEADINGS = ["references", "bibliography", "βιβλιογραφία", "αναφορές"]


def get_font_size(run):
    if run.font.size:
        return run.font.size.pt
    return None


def estimate_page(paragraph_number):
    try:
        return max(1, round(int(paragraph_number) / 9))
    except Exception:
        return "-"


def is_likely_math_or_symbol(run_text, font_name):
    if font_name in ALLOWED_MATH_FONTS:
        return True

    symbols = ["±", "≤", "≥", "μ", "β", "α", "γ", "δ", "CO₂", "CO2", "kg", "eq.", "≈", "×", "°"]
    if any(symbol in run_text for symbol in symbols):
        return True

    # many scientific values, e.g. 1.92 kg CO2, 23.26%, B.1.A
    if re.search(r"\d+(\.\d+)?\s?(kg|g|mg|%|CO2|CO₂|eq)", run_text):
        return True

    return False


def classify_paragraph(text, style):
    clean = text.strip()
    style_lower = style.lower()

    if style_lower.startswith("heading"):
        return "Heading"

    if clean.startswith(CAPTION_STARTS):
        return "Caption"

    if clean.lower() in REFERENCE_HEADINGS:
        return "References Heading"

    if style_lower in ["caption"]:
        return "Caption"

    if style_lower in ["normal", "body text"]:
        return "Body Text"

    return "Other"


def add_issue(issues, paragraph, category, severity, issue, expected, found, suggestion, text):
    issues.append({
        "Severity": severity,
        "Category": category,
        "Issue": issue,
        "Expected": expected,
        "Found": found,
        "Suggestion": suggestion,
        "Paragraph": paragraph,
        "Estimated page": estimate_page(paragraph),
        "Text": text[:160]
    })


def check_docx(file):
    doc = Document(file)
    issues = []

    previous_heading_level = None

    for p_index, paragraph in enumerate(doc.paragraphs, start=1):
        text = paragraph.text.strip()

        if not text:
            continue

        style = paragraph.style.name if paragraph.style else "Unknown"
        category = classify_paragraph(text, style)

        # Double spaces
        if "  " in text:
            add_issue(
                issues,
                p_index,
                category,
                "Warning",
                "Double spaces",
                "Single spaces between words",
                "Double spaces detected",
                "Remove extra spaces to improve consistency.",
                text
            )

        # Manual heading detection
        if text.isupper() and style == "Normal" and len(text) < 120:
            add_issue(
                issues,
                p_index,
                "Heading",
                "Warning",
                "Possible manual heading",
                "Use a Word Heading style",
                "Normal style",
                "Apply Heading 1, Heading 2, or Heading 3 instead of manual formatting.",
                text
            )

        # Heading hierarchy check
        if style.startswith("Heading"):
            match = re.search(r"Heading\s+(\d+)", style)
            if match:
                current_level = int(match.group(1))

                if previous_heading_level is not None:
                    if current_level > previous_heading_level + 1:
                        add_issue(
                            issues,
                            p_index,
                            "Heading",
                            "Critical",
                            "Skipped heading level",
                            f"Heading level should not jump from Heading {previous_heading_level} to Heading {current_level}",
                            style,
                            "Use a proper heading hierarchy, e.g. Heading 1 → Heading 2 → Heading 3.",
                            text
                        )

                previous_heading_level = current_level

        # Caption format check
        if category == "Caption":
            if text.startswith("Figure") and not re.match(r"^Figure\s+\d+[:.]\s+", text):
                add_issue(
                    issues,
                    p_index,
                    "Caption",
                    "Warning",
                    "Possible figure caption format issue",
                    "Figure X: Caption text",
                    text[:60],
                    "Use a consistent figure caption format, e.g. Figure 1: Description.",
                    text
                )

            if text.startswith("Table") and not re.match(r"^Table\s+\d+[:.]\s+", text):
                add_issue(
                    issues,
                    p_index,
                    "Caption",
                    "Warning",
                    "Possible table caption format issue",
                    "Table X: Caption text",
                    text[:60],
                    "Use a consistent table caption format, e.g. Table 1: Description.",
                    text
                )

        # Font and size checks only for body text
        if category == "Body Text":
            for run in paragraph.runs:
                run_text = run.text.strip()

                if not run_text:
                    continue

                font_name = run.font.name
                font_size = get_font_size(run)

                if is_likely_math_or_symbol(run_text, font_name):
                    continue

                if font_name and font_name != EXPECTED_FONT:
                    add_issue(
                        issues,
                        p_index,
                        category,
                        "Warning",
                        "Wrong font",
                        EXPECTED_FONT,
                        font_name,
                        "Use the expected font consistently in body text.",
                        text
                    )

                if font_size and font_size != EXPECTED_SIZE:
                    add_issue(
                        issues,
                        p_index,
                        category,
                        "Warning",
                        "Wrong font size",
                        f"{EXPECTED_SIZE} pt",
                        f"{font_size} pt",
                        "Use the expected font size consistently in body text.",
                        text
                    )

    return issues