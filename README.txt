SB-103 Dynamic 3×3 Generator — Streamlit Cloud fixed version

This version does NOT use ReportLab, so it avoids the
ModuleNotFoundError: reportlab problem.

Run:
pip install -r requirements.txt
streamlit run streamlit_app.py

Excel columns:
Post Office, Customer Name, Amount, Amount in Words
Optional: Account Number, Date

Output:
3 × 3 = 9 forms, 600-DPI PDF.
