"""Make the README pictures and video of the "sales since 1998" section on the dashboard:
assets/dashboard_page.png (top of the dashboard), assets/sales_history.png (the section, 2025),
assets/sales_history.mp4 and assets/sales_history.gif (the section stepping through every year, first before
inflation, then again in 2025 dollars).
Each frame is the real page opened at ?year=YYYY, so the video shows exactly what the page draws.
Requires: Google Chrome, pillow, imageio-ffmpeg (pip install pillow imageio-ffmpeg), and the docs folder served locally:
  python -m http.server 8791 --directory docs      then, from the repo root:  python analysis/build_sales_video.py
Not part of the CI checks, because it needs a browser.
"""
import os, subprocess, tempfile
import pandas as pd
from PIL import Image
import imageio_ffmpeg

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "http://localhost:8791/dashboard.html"
W, TOP, H = 1280, 668, 640   # the section starts 668px down the page at 1280px wide
years = list(pd.read_csv("data/sales_history.csv").year)
tmp = tempfile.mkdtemp()

def shot(year, out, top, height, real=False):
    """Open the page in a frame shifted up by `top`, so the part we want sits at the top of the picture.
    real=True opens it on "After inflation" (2025 dollars)."""
    frame = os.path.join(tmp, "frame.html")
    open(frame, "w").write(f'<body style="margin:0;overflow:hidden"><iframe src="{URL}?year={year}{"&real=1" if real else ""}" '
                           f'style="border:0;width:{W}px;height:{top + height}px;margin-top:-{top}px"></iframe></body>')
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-prefers-reduced-motion", "--force-color-profile=srgb",
                    f"--window-size={W},{height}", "--virtual-time-budget=3000", f"--user-data-dir={tmp}/profile",
                    f"--screenshot={out}", "file://" + frame], check=True, capture_output=True)

shot(years[-1], "assets/dashboard_page.png", 0, 1750)
shot(years[-1], "assets/sales_history.png", TOP, H)

def run(real):
    out = []
    for y in years:
        p = os.path.join(tmp, f"{y}{'r' if real else ''}.png"); shot(y, p, TOP, H, real); out.append(Image.open(p).convert("RGB"))
    return out
before, after = run(False), run(True)   # every year before inflation, then again in 2025 dollars
frames = before + [before[-1]] * 8 + after + [after[-1]] * 12   # 4 frames a second: hold 2 s, then 3 s at the end

writer = imageio_ffmpeg.write_frames("assets/sales_history.mp4", (W, H), fps=4, codec="libx264", pix_fmt_out="yuv420p",
                                     output_params=["-movflags", "+faststart"])
writer.send(None)
for f in frames:
    writer.send(f.tobytes())
writer.close()

small = [f.resize((W // 2, H // 2), Image.LANCZOS) for f in before + after]
hold = len(years) - 1
small[0].save("assets/sales_history.gif", save_all=True, append_images=small[1:], loop=0, optimize=True,
              duration=[250] * hold + [2000] + [250] * hold + [3000])
print("wrote assets/dashboard_page.png, sales_history.png, sales_history.mp4, sales_history.gif")
