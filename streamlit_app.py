
import io
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="SB-103 Dynamic 3×3", layout="wide")
st.title("SB-103 Dynamic 3×3 PDF Generator")
st.caption("Precisely aligned fields • 9 forms • 600-DPI output")

BASE = Path(__file__).parent
TEMPLATE = Image.open(BASE / "template.png").convert("RGB")
W, H = TEMPLATE.size
# The supplied template is 1110 × 1352. Coordinates below are calibrated to it.
SX, SY = W/1110, H/1352

def F(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, int(size*min(SX,SY)))
    return ImageFont.load_default()

def box(b):
    x1,y1,x2,y2=b
    return (round(x1*SX),round(y1*SY),round(x2*SX),round(y2*SY))

def fit(draw, text, maxw, size, bold=True):
    while size >= 9:
        f=F(size,bold)
        if draw.textbbox((0,0),text,font=f)[2] <= maxw:
            return f
        size -= 1
    return F(9,bold)

def write_center(draw, b, text, size=22, bold=True):
    x1,y1,x2,y2=box(b)
    f=fit(draw,text,x2-x1-8,size,bold)
    bb=draw.textbbox((0,0),text,font=f)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    draw.text((x1+(x2-x1-tw)/2,y1+(y2-y1-th)/2-2),text,font=f,fill="black")

def write_right(draw, b, text, size=22, bold=True):
    x1,y1,x2,y2=box(b)
    f=fit(draw,text,x2-x1-6,size,bold)
    bb=draw.textbbox((0,0),text,font=f)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    draw.text((x2-tw-3,y1+(y2-y1-th)/2-2),text,font=f,fill="black")

def white(draw,b):
    draw.rectangle(box(b),fill="white")

def form(r):
    im=TEMPLATE.copy()
    d=ImageDraw.Draw(im)

    po=str(r.get("Post Office","")).strip()
    name=str(r.get("Customer Name","")).strip()
    amount=str(r.get("Amount","")).strip()
    words=str(r.get("Amount in Words","")).strip()
    acc=str(r.get("Account Number","")).strip()
    date=str(r.get("Date","")).strip()

    # 1) Post office name: only replace PADALI B.O; preserve "Post Office".
    if po:
        white(d,(82,211,253,246))
        write_right(d,(82,211,253,246),po,21,True)

    # 2) Date: replace the placeholder characters, preserving the Date label/borders.
    if date:
        white(d,(575,207,1078,254))
        write_center(d,(575,207,1078,254),date,19,False)

    # 3) Account number: preserve the existing box grid; print centered across cells.
    if acc:
        white(d,(423,383,1073,430))
        # redraw the horizontal/vertical account box grid that was covered
        # by the white mask, matching the original thin line.
        d.rectangle(box((423,383,1073,430)),outline="black",width=max(1,round(1.2*SX)))
        # Recreate 12-character cell divisions approximately.
        for x in [474,529,584,639,694,749,804,859,914,969,1024]:
            xx=round(x*SX)
            d.line((xx,round(383*SY),xx,round(430*SY)),fill="black",width=max(1,round(1.2*SX)))
        write_center(d,(423,383,1073,430),acc,22,True)

    # 4) Customer name: aligned on the original underline, right side.
    if name:
        white(d,(676,484,1078,526))
        write_right(d,(676,484,1078,526),name,21,True)
        d.line((623*SX,518*SY,1078*SX,518*SY),fill="black",width=max(1,round(1.3*SX)))

    # 5) Amount in words: centered on its existing underline.
    if words:
        white(d,(448,536,1068,574))
        write_center(d,(448,536,1068,574),words.upper(),19,True)
        d.line((450*SX,568*SY,1060*SX,568*SY),fill="black",width=max(1,round(1.3*SX)))

    # 6) Amount: replace only the printed numeric value, preserving ₹, dots and slash.
    if amount:
        white(d,(900,632,1008,681))
        write_center(d,(900,632,1008,681),amount,27,True)

    return im

def make_sheet(rows):
    sheet=Image.new("RGB",(W*3,H*3),"white")
    for i in range(9):
        sheet.paste(form(rows[i] if i<len(rows) else {}),((i%3)*W,(i//3)*H))
    return sheet

def make_pdf(sheet):
    # The sheet is the same physical size as the earlier 300-DPI version.
    # Upscale 2×, then save the PDF at 600 DPI using Pillow only.
    hi = sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    hi.save(
        out,
        format="PDF",
        resolution=600.0,
        title="SB-103 3x3 - 600 DPI"
    )
    return out.getvalue()

st.subheader("Customer data")
uploaded=st.file_uploader("Optional Excel/CSV upload",type=["xlsx","xls","csv"])
if uploaded:
    if uploaded.name.lower().endswith(".csv"):
        df=pd.read_csv(uploaded,dtype=str).fillna("")
    else:
        df=pd.read_excel(uploaded,dtype=str).fillna("")
else:
    df=pd.DataFrame()

cols=["Post Office","Customer Name","Amount","Amount in Words","Account Number","Date"]
if df.empty:
    df=pd.DataFrame([{c:"" for c in cols} for _ in range(9)])
else:
    for c in cols:
        if c not in df.columns: df[c]=""
    df=df[cols].head(9).reindex(range(9)).fillna("")

edited=st.data_editor(df,num_rows="fixed",use_container_width=True,hide_index=True)

if st.button("Generate 3 × 3 • 600 DPI PDF",type="primary"):
    rows=edited.to_dict("records")
    sheet=make_sheet(rows)
    pdf=make_pdf(sheet)
    st.image(sheet.resize((min(1400,sheet.width), round(sheet.height*min(1400,sheet.width)/sheet.width))),caption="Alignment preview",use_container_width=True)
    st.download_button("Download 600-DPI PDF",pdf,"SB-103_3x3_600dpi.pdf","application/pdf")
