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
f_graph = F("DejaVuSans.ttf", 9)
f_cal_h = F("DejaVuSans-Bold.ttf", 11)

BLACK = 0
WHITE = 1

# ---- Divider ----
d.line((0, 88, W, 88), fill=BLACK)

# ---- Clock (top-left) ----
d.text((16, -7), "12:45", font=f_clock, fill=BLACK)

# ---- Date (two-line, bold, centered right) ----
d.text((580, 14), "Wednesday",   font=f_day,   fill=BLACK, anchor="ma")
d.text((580, 48), "September 26", font=f_month, fill=BLACK, anchor="ma")

# ---- Status stack (top-right) ----
d.text((772, 8),  "RSSI -68dBm", font=f_small, fill=BLACK, anchor="ra")
# ---- Battery bar (Ruuvi CR2477, right-aligned in status) ----
batt_v = 2.94
bvmin, bvmax = 2.0, 3.0          # CR2477: 2.0V empty -> 3.0V full
bf = max(0.0, min(1.0, (batt_v - bvmin) / (bvmax - bvmin)))
bb_w, bb_h = 44, 13
bbx0 = 772 - 2 - bb_w            # body left edge (2px nub on right)
bby = 30
d.rectangle((bbx0, bby, bbx0 + bb_w - 1, bby + bb_h - 1), outline=BLACK)          # body
d.rectangle((bbx0 + bb_w, bby + 3, bbx0 + bb_w + 2, bby + bb_h - 4), outline=BLACK)  # nub
fill_w = round((bb_w - 4) * bf)
d.rectangle((bbx0 + 2, bby + 2, bbx0 + 2 + fill_w - 1, bby + bb_h - 3), fill=BLACK)
d.text((bbx0 - 6, bby), "2.94V", font=f_small, fill=BLACK, anchor="ra")
d.text((772, 52), "Move 137",    font=f_small, fill=BLACK, anchor="ra")

# ---- Calendar (centered between clock and date) ----
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
        day = w * 7 + c - 3   # Oct 1 = Thursday = col 4
        if day < 1 or day > 31:
            continue
        x0 = cx0 + c * cw
        y0 = cy0 + (w + 1) * rh
        if day == 6:          # Oct 6 = today -> filled
            d.rectangle((x0 + 1, y0 + 1, x0 + cw - 1, y0 + rh - 1), fill=BLACK)
        else:
            d.rectangle((x0 + 1, y0 + 1, x0 + cw - 1, y0 + rh - 1), outline=BLACK)

# ---- Top divider ticks (up, halfway: y=44..88) ----
for tx in (308, 505, 664):
    d.line((tx, 44, tx, 88), fill=BLACK)

# ---- Weather icon (sunny U+F00D) ----
d.text((72, 96), "\uF00D", font=f_icon, fill=BLACK, anchor="ma")

# ---- Temperature (number + superscript unit) ----
num = "75"
nw = d.textlength(num, font=f_temp)      # ~161 @ 116px
temp_cx = 270                             # centered between icon and 1st bar
d.text((temp_cx, 96), num, font=f_temp, fill=BLACK, anchor="ma")
d.text((temp_cx + nw / 2 + 4, 96), "\u00B0F", font=f_unit, fill=BLACK, anchor="la")

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

bar(445, "HMD", 42, 0, 100, "42%", None)
bar(545, "PRS", 29.97, 28.0, 32.0, "29.97", "inHg")
bar(645, "DPT", 48, -20, 100, "48\u00B0F", None)
bar(745, "TMP", 75, -40, 120, "75\u00B0F", None)

# ---- Bottom divider ticks (down, halfway: y=88..132) ----
for bx in (156, 495, 595, 695):
    d.line((bx, 88, bx, 132), fill=BLACK)

# ---- 14-day pressure graph ----
gx0, gy0, gx1, gy1 = 8, 222, 784, 268
d.text((gx0 + 4, gy0 - 2), "14 DAYS", font=f_graph, fill=BLACK)
d.line((gx0, gy1, gx1, gy1), fill=BLACK)
d.line((gx0, gy0, gx0, gy1), fill=BLACK)
pmin, pmax = 29.2, 30.2
p = [29.85, 29.6, 29.7, 29.97, 29.8, 29.5, 29.6, 29.7, 29.65, 29.75, 29.55, 29.9, 29.8, 29.7]
for i in range(13):
    xa = gx0 + i * (gx1 - gx0) // 13
    ya = gy1 - int((p[i] - pmin) / (pmax - pmin) * (gy1 - gy0))
    xb = gx0 + (i + 1) * (gx1 - gx0) // 13
    yb = gy1 - int((p[i + 1] - pmin) / (pmax - pmin) * (gy1 - gy0))
    d.line((xa, ya, xb, yb), fill=BLACK)
d.text((gx0, 250), "29.2", font=f_graph, fill=BLACK)
d.text((gx0, gy0 - 10), "30.2", font=f_graph, fill=BLACK)

img.save("/home/sharby/repos/weather-paper/preview/main_calendar.png")
print("saved")
