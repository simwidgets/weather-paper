from PIL import Image, ImageDraw, ImageFont

W, H = 792, 272
img = Image.new("1", (W, H), 1)  # 1 = white
d = ImageDraw.Draw(img)

FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
def F(name, size):
    return ImageFont.truetype(FD + name, size)

f_clock = F("DejaVuSans-Bold.ttf", 90)
f_day   = F("DejaVuSans-Bold.ttf", 22)
f_month = F("DejaVuSans-Bold.ttf", 18)
f_small = F("DejaVuSans.ttf", 14)
f_icon  = F("weathericons.ttf", 90)
f_temp  = F("DejaVuSans-Bold.ttf", 116)
f_unit  = F("DejaVuSans-Bold.ttf", 42)
f_meas  = F("DejaVuSans.ttf", 16)
f_label = F("DejaVuSans-Bold.ttf", 13)
f_cal_h = F("DejaVuSans-Bold.ttf", 11)
f_mdi   = F("mdi.ttf", 18)

# forecast strip fonts
f_ficon  = F("weathericons.ttf", 48)
f_fday   = F("DejaVuSans-Bold.ttf", 12)
f_fhi    = F("DejaVuSans-Bold.ttf", 14)
f_flo    = F("DejaVuSans.ttf", 11)

BLACK = 0

# ---- Divider ----
d.line((0, 88, W, 88), fill=BLACK)

# ---- Clock (top-left) ----
d.text((16, -7), "12:45", font=f_clock, fill=BLACK)

# ---- Date (two-line, bold, centered right) ----
d.text((580, 14), "Wednesday", font=f_day,   fill=BLACK, anchor="ma")
d.text((580, 48), "October 7",  font=f_month, fill=BLACK, anchor="ma")

# ---- Status stack (top-right) ----
d.text((772, 8),  "RSSI -68dBm", font=f_small, fill=BLACK, anchor="ra")
batt_v = 2.94
bf = max(0.0, min(1.0, (batt_v - 2.0) / (3.0 - 2.0)))
bb_w, bb_h = 44, 13
bbx0 = 772 - 2 - bb_w
bby = 30
d.rectangle((bbx0, bby, bbx0 + bb_w - 1, bby + bb_h - 1), outline=BLACK)
d.rectangle((bbx0 + bb_w, bby + 3, bbx0 + bb_w + 2, bby + bb_h - 4), outline=BLACK)
fill_w = round((bb_w - 4) * bf)
d.rectangle((bbx0 + 2, bby + 2, bbx0 + 2 + fill_w - 1, bby + bb_h - 3), fill=BLACK)
d.text((bbx0 - 6, bby), "2.94V", font=f_small, fill=BLACK, anchor="ra")
d.text((772, 52), "Move 137", font=f_small, fill=BLACK, anchor="ra")
d.text((772, 70), "WiFi 3s",   font=f_small, fill=BLACK, anchor="ra")

# ---- WiFi icon: bottom-left of the status box (left of Move, lower) ----
d.text((668, 66), "\U000F05A9", font=f_mdi, fill=BLACK, anchor="la")

# ---- Calendar (centered) ----
cx0, cx1 = 314, 496
cy0, cy1 = 6, 86
ncol = 7
cw = (cx1 - cx0) / ncol
rh = (cy1 - cy0) / 6
days = "SMTWTFS"
hx = cx0 + cw / 2
for i, ch in enumerate(days):
    d.text((hx + i * cw, cy0 - 1), ch, font=f_cal_h, fill=BLACK, anchor="ma")
for w in range(5):
    for c in range(ncol):
        day = w * 7 + c - 2   # Oct 7 = Wednesday = col 3
        if day < 1 or day > 31:
            continue
        x0 = cx0 + c * cw
        y0 = cy0 + (w + 1) * rh
        if day == 7:
            d.rectangle((x0 + 1, y0 + 1, x0 + cw - 1, y0 + rh - 1), fill=BLACK)
        else:
            d.rectangle((x0 + 1, y0 + 1, x0 + cw - 1, y0 + rh - 1), outline=BLACK)

# ---- Top divider ticks ----
for tx in (308, 505, 664):
    d.line((tx, 44, tx, 88), fill=BLACK)

# ---- Weather icon (centered vertically between divider 88 and forecast line 214) ----
d.text((72, 86), "\uF00D", font=f_icon, fill=BLACK, anchor="ma")

# ---- Temperature (number + superscript unit) ----
num = "79"
nw = d.textlength(num, font=f_temp)
temp_cx = 270
d.text((temp_cx, 96), num, font=f_temp, fill=BLACK, anchor="ma")
d.text((temp_cx + nw / 2 + 4, 96), "\u00B0F", font=f_unit, fill=BLACK, anchor="la")

# ---- Zip code: below divider, top a few px above the degF unit ----
d.text((temp_cx, 96), "52404", font=f_month, fill=BLACK, anchor="ma")

# ---- Four vertical bar meters ----
def bar(cx, lab, val, vmin, vmax, v1, v2):
    x0, x1, top, bot, wb = cx - 26, cx + 26, 104, 186, 4
    d.text((cx, 90), lab, font=f_label, fill=BLACK, anchor="ma")
    d.rectangle((x0, top, x1, bot), outline=BLACK)
    frac = max(0.0, min(1.0, (val - vmin) / (vmax - vmin)))
    fillable = (bot - wb) - (top + wb)
    fy = (bot - wb) - int(frac * fillable)
    d.rectangle((x0 + wb, fy, x1 - wb, bot - wb), fill=BLACK)
    for i in range(11):
        ty = top + i * (bot - top) // 10
        d.line((x0 - 7, ty, x0 - 2, ty), fill=BLACK)
    if v2:
        d.text((cx, 188), v1, font=f_meas, fill=BLACK, anchor="ma")
        d.text((cx, 204), v2, font=f_small, fill=BLACK, anchor="ma")
    else:
        d.text((cx, 194), v1, font=f_meas, fill=BLACK, anchor="ma")

bar(445, "HMD", 53, 0, 100, "53%", None)
bar(545, "PRS", 29.1, 28.0, 32.0, "29.11 inHg", None)
bar(645, "DPT", 55, -20, 100, "55\u00B0F", None)
bar(745, "TMP", 79, -40, 120, "79\u00B0F", None)

# ---- Bottom divider ticks ----
for bx in (156, 495, 595, 695):
    d.line((bx, 88, bx, 132), fill=BLACK)

# ==================== 7-DAY FORECAST STRIP (tomorrow onward) ====================
line_y = 214
gx0, gx1 = 8, 784
d.line((gx0, line_y, gx1, line_y), fill=BLACK)

ncols = 7
colw = (gx1 - gx0) / ncols

# 6 vertical separators, half-height
for i in range(1, ncols):
    sx = gx0 + i * colw
    d.line((sx, line_y, sx, line_y + 29), fill=BLACK)

days  = ["THU", "FRI", "SAT", "SUN", "MON", "TUE", "WED"]
codes = ["\uF013", "\uF019", "\uF013", "\uF013", "\uF019", "\uF019", "\uF019"]
hi    = ["73", "76", "80", "76", "78", "58", "60"]
lo    = ["49", "56", "60", "58", "61", "46", "43"]

for i in range(ncols):
    x0 = gx0 + i * colw
    d.text((x0 + 8, line_y), codes[i], font=f_ficon, fill=BLACK, anchor="la")
    d.text((x0 + 58, line_y + 2), days[i], font=f_fday, fill=BLACK, anchor="la")
    cx = x0 + 83
    d.text((cx, line_y + 21), hi[i] + "\u00B0", font=f_fhi, fill=BLACK, anchor="ma")
    d.text((cx, line_y + 40), lo[i] + "\u00B0", font=f_flo, fill=BLACK, anchor="ma")

img.save("/home/sharby/repos/weather-paper/preview/forecast.png")
print("saved")
