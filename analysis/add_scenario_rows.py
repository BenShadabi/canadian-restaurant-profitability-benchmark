"""One-off helper that added the conservative case and the per-1% lever table to the Scenario tab of
data/Canadian_Restaurant_Benchmark.xlsx. It edits the sheet XML directly so the four charts in the workbook are kept
(openpyxl would drop them). It does nothing if the rows are already there.
Run from the repo root:  python analysis/add_scenario_rows.py
"""
import re, shutil, zipfile
from xml.sax.saxutils import escape

PATH = "data/Canadian_Restaurant_Benchmark.xlsx"
SHEET = "xl/worksheets/sheet4.xml"  # the Scenario tab
ROW = '<row r="{r}" customFormat="false" ht="15" hidden="false" customHeight="false" outlineLevel="0" collapsed="false">{cells}</row>'

def text(ref, style, s):
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(s)}</t></is></c>'

def formula(ref, style, f, v):
    return f'<c r="{ref}" s="{style}" t="n"><f aca="false">{escape(f)}</f><v>{v}</v></c>'

# cached values are the same numbers the CSVs give: checks.py compares them
rows = [
    (27, text("A27", 13, "Conservative case: overhead cut on the published utilities line only")),
    (28, text("A28", 15, "Overhead reduction, utilities and telecom only") + formula("B28", 17, "B6", 0.15)
         + formula("C28", 27, "Benchmark!B9*B28", 3225) + text("D28", 15, "Utilities x cut. Leaves out the calculated other expenses line.")),
    (29, text("A29", 25, "Total profit improvement (conservative)") + formula("C29", 27, "C5+C28+C8", 27049)),
    (30, text("A30", 15, "Profit after (conservative)") + formula("C30", 27, "C11+C29", 48549)),
    (31, text("A31", 15, "Margin after (conservative)") + formula("C31", 17, "C30/Benchmark!B5", 48549 / 849200)),
    (32, text("A32", 15, "Part of the headline overhead gain that comes from the calculated other expenses line")
         + formula("C32", 27, "Benchmark!B11*B6", 19620)),
    (34, text("A34", 13, "Profit gain from a 1% cut in each cost line")),
    (35, text("A35", 15, "Cost of sales") + formula("C35", 27, "Benchmark!B6*0.01", 3804)),
    (36, text("A36", 15, "Labour") + formula("C36", 27, "Benchmark!B7*0.01", 2002)),
    (37, text("A37", 15, "Overhead (utilities + calculated other)") + formula("C37", 27, "(Benchmark!B9+Benchmark!B11)*0.01", 1523)),
]

zin = zipfile.ZipFile(PATH)
xml = zin.read(SHEET).decode("utf-8")
if 'r="A27"' in xml:
    print("rows already added, nothing to do")
else:
    xml = xml.replace("</sheetData>", "".join(ROW.format(r=r, cells=c) for r, c in rows) + "</sheetData>", 1)
    xml = xml.replace('<dimension ref="A1:D25"/>', '<dimension ref="A1:D37"/>', 1)
    tmp = PATH + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, xml.encode("utf-8") if item.filename == SHEET else zin.read(item.filename))
    zin.close()
    shutil.move(tmp, PATH)
    print("added conservative case and per-1% rows to the Scenario tab")
