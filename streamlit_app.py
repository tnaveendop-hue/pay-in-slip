
import io
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="SB-103 Dynamic Generator", layout="wide")

BASE = Path(__file__).parent
TEMPLATE = Image.open(BASE / "template.png").convert("RGB")
W, H = TEMPLATE.size

st.title("SB-103 Dynamic 3×3 PDF Generator")
st.write("Enter customer details below. The PDF will use the entered values — not the sample values from the template.")

def get_font(size, bold=False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in names:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fit_font(draw, text, max_width, size, bold=True):
    s = size
    while s >= 9:
        f = get_font(s, bold)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
        s -= 1
    return get_font(9, bold)

def erase(draw, xy):
    draw.rectangle(xy, fill="white")

def centered(draw, xy, text, size=20, bold=True):
    x1,y1,x2,y2 = xy
    f = fit_font(draw, text, x2-x1-8, size, bold)
    b = draw.textbbox((0,0), text, font=f)
    tw, th = b[2]-b[0], b[3]-b[1]
    draw.text(
        (x1+(x2-x1-tw)/2, y1+(y2-y1-th)/2-2),
        text, fill="black", font=f
    )

def right_aligned(draw, xy, text, size=20, bold=True):
    x1,y1,x2,y2 = xy
    f = fit_font(draw, text, x2-x1-8, size, bold)
    b = draw.textbbox((0,0), text, font=f)
    tw, th = b[2]-b[0], b[3]-b[1]
    draw.text(
        (x2-tw-4, y1+(y2-y1-th)/2-2),
        text, fill="black", font=f
    )

def make_form(row):
    im = TEMPLATE.copy()
    d = ImageDraw.Draw(im)

    post = str(row.get("Post Office", "")).strip()
    customer = str(row.get("Customer Name", "")).strip()
    amount = str(row.get("Amount", "")).strip()
    words = str(row.get("Amount in Words", "")).strip()
    account = str(row.get("Account Number", "")).strip()
    date = str(row.get("Date", "")).strip()

    # These coordinates are calibrated directly to the supplied 1127×1396 template.

    # POST OFFICE: replace only PADALI B.O, keep "Post Office".
    if post:
        erase(d, (82, 210, 260, 247))
        right_aligned(d, (82, 210, 260, 247), post, 20, True)

    # DATE: replace placeholder date boxes' content without covering borders.
    if date:
        erase(d, (585, 210, 1085, 252))
        centered(d, (585, 210, 1085, 252), date, 18, False)

    # ACCOUNT NUMBER: clear existing sample/content area and redraw cells.
    if account:
        erase(d, (423, 373, 1080, 432))
        # Original account-number box boundary
        d.rectangle((423, 373, 1080, 432), outline="black", width=2)
        # Approximate original cell divisions
        for x in [476, 531, 586, 641, 696, 751, 806, 861, 916, 971, 1026]:
            d.line((x, 373, x, 432), fill="black", width=2)
        centered(d, (423, 373, 1080, 432), account, 22, True)

    # CUSTOMER NAME: clear old SAVARA... and place new name on line.
    if customer:
        erase(d, (670, 480, 1085, 530))
        # Restore underline
        d.line((625, 518, 1080, 518), fill="black", width=2)
        right_aligned(d, (670, 480, 1080, 515), customer, 21, True)

    # AMOUNT IN WORDS: clear old sample and place new text.
    if words:
        erase(d, (445, 535, 1068, 575))
        d.line((450, 570, 1060, 570), fill="black", width=2)
        centered(d, (445, 535, 1068, 567), words.upper(), 19, True)

    # AMOUNT: clear old 110 only. Keep ₹, dots and slash.
    if amount:
        erase(d, (895, 632, 1015, 680))
        centered(d, (895, 632, 1015, 680), amount, 27, True)

    return im

def make_sheet(rows):
    sheet = Image.new("RGB", (W*3, H*3), "white")
    for i in range(9):
        row = rows[i] if i < len(rows) else {}
        sheet.paste(make_form(row), ((i % 3)*W, (i // 3)*H))
    return sheet

def make_600dpi_pdf(sheet):
    # 2× raster from the 300-DPI physical layout = 600 DPI.
    hi = sheet.resize((sheet.width*2, sheet.height*2), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    hi.save(out, format="PDF", resolution=600.0, title="SB-103 3x3 600 DPI")
    return out.getvalue()

columns = ["Post Office", "Customer Name", "Amount", "Amount in Words", "Account Number", "Date"]

uploaded = st.file_uploader(
    "Optional: upload Excel/CSV",
    type=["xlsx", "xls", "csv"]
)

if uploaded:
    try:
        if uploaded.name.lower().endswith(".csv"):
            data = pd.read_csv(uploaded, dtype=str).fillna("")
        else:
            data = pd.read_excel(uploaded, dtype=str).fillna("")
        for c in columns:
            if c not in data.columns:
                data[c] = ""
        data = data[columns].head(9).reindex(range(9)).fillna("")
        st.success("Data loaded. Check the table before generating.")
    except Exception as e:
        st.error(f"Could not read Excel/CSV: {e}")
        data = pd.DataFrame([{c:"" for c in columns} for _ in range(9)])
else:
    data = pd.DataFrame([{c:"" for c in columns} for _ in range(9)])

edited = st.data_editor(
    data,
    num_rows="fixed",
    hide_index=True,
    use_container_width=True,
    key="customer_data",
)

if st.button("Generate PDF — 3 × 3 — 600 DPI", type="primary"):
    rows = edited.to_dict("records")

    # Make sure the generated form uses the CURRENT table values.
    sheet = make_sheet(rows)

    st.subheader("Preview")
    preview = sheet.copy()
    preview.thumbnail((1400, 1400))
    st.image(preview, use_container_width=True)

    pdf_bytes = make_600dpi_pdf(sheet)

    st.download_button(
        "Download 600-DPI PDF",
        data=pdf_bytes,
        file_name="SB-103_3x3_600dpi.pdf",
        mime="application/pdf"
    )
