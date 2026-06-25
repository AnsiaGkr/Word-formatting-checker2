import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path
import base64

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from checker import check_docx


BUSINESS_EMAIL = "studentdimension@gmail.com"
BUSINESS_SITE = "https://student-dimension.webnode.gr/"
LOGO_PATH = "logo.png"
PRICE = "19.90€"
IRIS_PHONE = "6976928170"


def load_access_codes():
    try:
        df = pd.read_csv("codes.csv")
        return df[df["active"].str.lower() == "yes"]["code"].astype(str).tolist()
    except Exception:
        return []


def estimate_page(paragraph_number):
    try:
        return max(1, round(int(paragraph_number) / 9))
    except Exception:
        return "-"


def safe_text(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def logo_to_base64(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def get_logo_image(path, max_width=150, max_height=80):
    img_reader = ImageReader(path)
    img_width, img_height = img_reader.getSize()
    ratio = min(max_width / img_width, max_height / img_height)
    return Image(path, width=img_width * ratio, height=img_height * ratio)


def create_pdf_report(issues, report_title, brand_color):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=colors.HexColor(brand_color),
        fontSize=22,
        leading=26,
        alignment=1,
        spaceAfter=10
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=1
    )

    left_style = ParagraphStyle(
        "LeftCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=0
    )

    section_style = ParagraphStyle(
        "IssueTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor(brand_color),
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=6
    )

    story = []

    if Path(LOGO_PATH).exists():
        logo = get_logo_image(LOGO_PATH)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 12))

    story.append(Paragraph("Word Formatting Checker", title_style))
    story.append(Paragraph("Created by Student Dimension", normal_style))
    story.append(Paragraph(f"Email: {BUSINESS_EMAIL}", normal_style))
    story.append(Paragraph(f"Website: {BUSINESS_SITE}", normal_style))
    story.append(Spacer(1, 22))

    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(f"Total issues found: <b>{len(issues)}</b>", normal_style))
    story.append(Spacer(1, 14))

    summary_data = [["Issue type", "Count"]]

    if issues:
        issue_counts = pd.DataFrame(issues)["Issue"].value_counts().reset_index()
        issue_counts.columns = ["Issue type", "Count"]
        summary_data.extend(issue_counts.values.tolist())

    summary_table = Table(summary_data, colWidths=[300, 80])
    summary_table.hAlign = "CENTER"
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(brand_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 18))

    for index, issue in enumerate(issues, start=1):
        paragraph = issue.get("Paragraph", "-")
        estimated_page = estimate_page(paragraph)
        text = safe_text(issue.get("Text", ""))

        story.append(Paragraph(f"Issue #{index}: {safe_text(issue.get('Issue', ''))}", section_style))
        story.append(Paragraph(f"<b>Estimated page:</b> {estimated_page}", left_style))
        story.append(Paragraph(f"<b>Paragraph:</b> {paragraph}", left_style))
        story.append(Paragraph(f"<b>Expected:</b> {safe_text(issue.get('Expected', ''))}", left_style))
        story.append(Paragraph(f"<b>Found:</b> {safe_text(issue.get('Found', ''))}", left_style))
        story.append(Paragraph(f"<b>Text preview:</b> {text}", left_style))
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Created by Student Dimension", normal_style))
    story.append(Paragraph(f"{BUSINESS_EMAIL} | {BUSINESS_SITE}", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


st.set_page_config(
    page_title="Word Formatting Checker | Student Dimension",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

.hero {
    background: linear-gradient(135deg, #f3f0ff 0%, #ffffff 100%);
    padding: 2.5rem;
    border-radius: 24px;
    border: 1px solid #e5ddff;
    text-align: center;
    margin-bottom: 2rem;
}

.hero-logo {
    width: 150px;
    margin-bottom: 1.2rem;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 0.8rem;
}

.hero p {
    font-size: 1.1rem;
}

.price-box {
    background: #ffffff;
    border: 1px solid #e6e1f5;
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
}

.feature-box {
    background: #ffffff;
    border: 1px solid #eee;
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.7rem;
    font-size: 1.05rem;
}

.contact-box {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid #eee;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}

.payment-phone {
    background: #f3f0ff;
    border: 1px solid #d8cdfc;
    border-radius: 14px;
    padding: 0.9rem;
    font-size: 1.35rem;
    font-weight: bold;
    color: #4b2f91;
    margin: 1rem 0;
}

.mail-button {
    display: inline-block;
    background-color: #6C4AB6;
    color: white !important;
    padding: 0.95rem 1.6rem;
    border-radius: 12px;
    text-decoration: none;
    font-weight: bold;
    margin-top: 1rem;
}

.mail-button:hover {
    background-color: #56389c;
}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.header("⚙️ Settings")
    report_title = st.text_input("PDF report title", "Formatting Report")
    report_filename = st.text_input("PDF file name", "student_dimension_formatting_report.pdf")
    brand_color = st.color_picker("Brand color", "#6C4AB6")


logo_base64 = logo_to_base64(LOGO_PATH)

if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="hero-logo">'
else:
    logo_html = ""

st.markdown(f"""
<div class="hero">
    {logo_html}
    <h1>Word Formatting Checker</h1>
    <p>Avoid formatting mistakes before submitting your thesis, dissertation or academic report.</p>
    <p><b>Created by Student Dimension</b></p>
</div>
""", unsafe_allow_html=True)


col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="feature-box">✓ Check fonts</div>
    <div class="feature-box">✓ Check spacing</div>
    <div class="feature-box">✓ Check headings</div>
    <div class="feature-box">✓ Generate PDF report</div>
    <div class="feature-box">✓ Detect formatting inconsistencies</div>
    """, unsafe_allow_html=True)


if "show_payment" not in st.session_state:
    st.session_state.show_payment = False


with col2:
    st.markdown(f"""
    <div class="price-box">
        <h2>{PRICE}</h2>
        <p>One access code</p>
        <p style="font-size:0.9rem;">
            Ideal for theses, dissertations and academic reports.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🟣 Pay via IRIS", use_container_width=True):
        st.session_state.show_payment = True

    if st.session_state.show_payment:
        st.markdown(f"""
        <div class="price-box">
            <p><b>Send the payment to:</b></p>
            <div class="payment-phone">{IRIS_PHONE}</div>
            <p style="font-size:0.85rem;">
                After payment, send your proof of payment by email to receive your access code.
            </p>
            <a class="mail-button"
               href="mailto:{BUSINESS_EMAIL}?subject=Word Formatting Checker Payment&body=Hello Student Dimension,%0D%0AI have completed my payment for the Word Formatting Checker.%0D%0DPlease find my payment proof attached.%0D%0DThank you."
               target="_blank">
               ✅ I have completed my payment
            </a>
        </div>
        """, unsafe_allow_html=True)


st.markdown(f"""
<div class="contact-box">
    <b>Email:</b> {BUSINESS_EMAIL}<br>
    <b>Website:</b> <a href="{BUSINESS_SITE}" target="_blank">{BUSINESS_SITE}</a>
</div>
""", unsafe_allow_html=True)


if "access_granted" not in st.session_state:
    st.session_state.access_granted = False

access_codes = load_access_codes()

st.divider()

if not st.session_state.access_granted:
    st.subheader("🔐 Already have an access code?")
    code = st.text_input("Enter your access code", type="password")

    if st.button("Unlock"):
        if code in access_codes:
            st.session_state.access_granted = True
            st.success("Access granted.")
            st.rerun()
        else:
            st.error("Invalid access code.")

else:
    st.success("Access granted.")

    uploaded_file = st.file_uploader("Upload your .docx file", type=["docx"])

    if uploaded_file is not None:
        st.info("File uploaded successfully.")

        if st.button("Check formatting", type="primary"):
            issues = check_docx(uploaded_file)

            if not issues:
                st.success("✅ No formatting issues found.")
            else:
                st.error(f"Found {len(issues)} possible issues.")

                df = pd.DataFrame(issues)

                st.subheader("📊 Summary")
                summary = df["Issue"].value_counts().reset_index()
                summary.columns = ["Issue type", "Count"]
                st.dataframe(summary, use_container_width=True)

                st.subheader("📋 Detailed report")
                st.dataframe(df, use_container_width=True)

                pdf_report = create_pdf_report(
                    issues,
                    report_title=report_title,
                    brand_color=brand_color
                )

                st.download_button(
                    label="Download PDF report",
                    data=pdf_report,
                    file_name=report_filename,
                    mime="application/pdf"
                )