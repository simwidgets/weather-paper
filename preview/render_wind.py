from PIL import Image, ImageDraw, ImageFont
import math

W, H = 792, 272
img = Image.new("1", (W, H), 1)
d = ImageDraw.Draw(img)

FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
def F(name, size):
    return ImageFont.truetype(FD + name, size)

f_clock = F("DejaVuSans-Bold.ttf", 90)
f_day   = F("DejaVuSans-Bold.ttf", 22)
f_month = F("DejaVuSans-Bold.ttf", 18)
f_small = F("DejaVuSans.ttf", 14)
f_icon  = F("weathericons.ttf", 90)
f_temp  = F("DejaVuSans-Bold.ttf", 132)
f_unit  = F("DejaVuSans-Bold.ttf", 42)
f_meas  = F("DejaVuSans.ttf", 16)
f_label = F("DejaVuSans-Bold.ttf", 13)
f_cal_h = F("DejaVuSans-Bold.ttf", 11)
f_wx    = F("DejaVuSans.ttf", 12)
f_zip   = F("DejaVuSans-Bold.ttf", 18)
f_sta   = F("DejaVuSans-Bold.ttf", 14)
f_src   = F("mdi.ttf", 20)
f_card  = F("DejaVuSans-Bold.ttf", 16)
f_mph   = F("DejaVuSans-Bold.ttf", 30)
f_ficon = F("weathericons.ttf", 48)
f_fday  = F("DejaVuSans-Bold.ttf", 12)
f_fhi   = F("DejaVuSans-Bold.ttf", 14)
f_flo   = F("DejaVuSans.ttf", 11)

BLACK = 0

# ---- Divider ----
d.line((0, 88, W, 88), fill=BLACK)

# ---- Clock ----
d.text((16, -7), "12:45", font=f_clock, fill=BLACK)

# ---- Date ----
d.text((580, 14), "Wednesday", font=f_day, fill=BLACK, anchor="ma")
d.text((580, 48), "October 7", font=f_month, fill=BLACK, anchor="ma")

# ---- Status stack (non-Ruuvi) ----
d.text((772, 10), "RSSI -68dBm", font=f_small, fill=BLACK, anchor="ra")
d.text((772, 30), "--", font=f_small, fill=BLACK, anchor="ra")
d.text((772, 54), "--", font=f_small, fill=BLACK, anchor="ra")
d.text((772, 70), "WiFi 30s", font=f_small, fill=BLACK, anchor="ra")
d.text((668, 26), "WX: 10/06 @ 18:01", font=f_wx, fill=BLACK, anchor="la")
d.text((668, 46), "52404", font=f_zip, fill=BLACK, anchor="la")
d.text((791, 46), "KCID", font=f_sta, fill=BLACK, anchor="ra")
d.text((668, 66), "\U000F05A9", font=f_src, fill=BLACK, anchor="la")

# ---- Calendar ----
cx0, cx1 = 314, 496
cy0, cy1 = 6, 86
cw = (cx1 - cx0) / 7
rh = (cy1 - cy0) / 6
for i, ch in enumerate("SMTWTFS"):
    d.text((cx0 + cw/2 + i*cw, cy0 - 1), ch, font=f_cal_h, fill=BLACK, anchor="ma")
for w in range(5):
    for c in range(7):
        day = w*7 + c - 2
        if day < 1 or day > 31:
            continue
        x0 = cx0 + c*cw
        y0 = cy0 + (w+1)*rh
        if day == 7:
            d.rectangle((x0+1, y0+1, x0+cw-1, y0+rh-1), fill=BLACK)
        else:
            d.rectangle((x0+1, y0+1, x0+cw-1, y0+rh-1), outline=BLACK)

for tx in (308, 505, 664):
    d.line((tx, 44, tx, 88), fill=BLACK)

# ---- Weather icon: centered vertically between divider and forecast ----
band_mid = (88 + 214) / 2
icon_bbox = d.textbbox((0, 0), "\uF00D", font=f_icon)
icon_x = 72 - (icon_bbox[0] + icon_bbox[2]) / 2
icon_y = band_mid - (icon_bbox[1] + icon_bbox[3]) / 2
d.text((icon_x, icon_y), "\uF00D", font=f_icon, fill=BLACK, anchor="la")
d.text((1, 88), "10%", font=f_sta, fill=BLACK, anchor="la")

# ---- Temperature: digits centered vertically between divider (88) and forecast (214) ----
num = "75"
nw = d.textlength(num, font=f_temp)
uw = d.textlength("\u00B0F", font=f_unit)
temp_cx = 270
temp_f_right = temp_cx + nw/2 + 4 + uw     # right edge of degF
bbox = d.textbbox((0, 0), num, font=f_temp)
temp_top_y = band_mid - (bbox[1] + bbox[3]) / 2
d.text((temp_cx - nw/2, temp_top_y), num, font=f_temp, fill=BLACK, anchor="la")
# degF: top-right corner of the temp, 4px padding from the top and right ink edges
ubbox = d.textbbox((0, 0), "\u00B0F", font=f_unit)
degF_x = (temp_cx + nw/2 + 4) - ubbox[0]
degF_y = (temp_top_y + bbox[1] + 4) - ubbox[1]
d.text((degF_x, degF_y), "\u00B0F", font=f_unit, fill=BLACK, anchor="la")

# ---- Bars (thin, close) ----
bar_w = 32
def bar(cx, lab, val, vmin, vmax, v1):
    x0, x1, top, bot, wb = cx - bar_w//2, cx + bar_w//2, 104, 186, 3
    d.text((cx, 90), lab, font=f_label, fill=BLACK, anchor="ma")
    d.rectangle((x0, top, x1, bot), outline=BLACK)
    frac = max(0.0, min(1.0, (val - vmin) / (vmax - vmin)))
    fillable = (bot - wb) - (top + wb)
    fy = (bot - wb) - int(frac * fillable)
    d.rectangle((x0 + wb, fy, x1 - wb, bot - wb), fill=BLACK)
    for i in range(11):
        ty = top + i * (bot - top) // 10
        d.line((x0 - 7, ty, x0 - 2, ty), fill=BLACK)
    d.text((cx, 194), v1, font=f_meas, fill=BLACK, anchor="ma")

bar(556, "HMD", 42, 0, 100, "42%")
bar(624, "PRS", 29.97, 28.0, 32.0, "29.97 in")
bar(692, "DPT", 48, -20, 100, "48\u00B0F")
bar(760, "FEEL", 75, -40, 120, "75\u00B0F")

# ---- WIND DIAL: divider centered between degF-end and W-start; dial centered between divider and first bar ----
wr = 38
d_lab = 10
bar_tick_x = (556 - bar_w//2) - 7        # 533
w_hw = d.textlength("W", font=f_card) / 2
# solve: divider = (temp_f_right + W_left)/2, dial_cx = (divider + bar_tick_x)/2, W_left = dial_cx - wr - d_lab - w_hw
dial_cx = (temp_f_right - wr - d_lab - w_hw + 2*bar_tick_x) / 3
W_left = dial_cx - wr - d_lab - w_hw
divider_x = (temp_f_right + W_left) / 2
wcy = band_mid
d.ellipse((dial_cx-wr, wcy-wr, dial_cx+wr, wcy+wr), outline=BLACK)
d.text((dial_cx, wcy - wr - 11), "N", font=f_card, fill=BLACK, anchor="mm")
d.text((dial_cx, wcy + wr + 11), "S", font=f_card, fill=BLACK, anchor="mm")
d.text((dial_cx + wr + 11, wcy), "E", font=f_card, fill=BLACK, anchor="mm")
d.text((dial_cx - wr - 11, wcy), "W", font=f_card, fill=BLACK, anchor="mm")
deg = 225
rad = math.radians(deg)
u = (math.sin(rad), -math.cos(rad))     # outward radial unit vector
v = (math.cos(rad), math.sin(rad))      # perpendicular
tip = (dial_cx + (wr - 7) * u[0], wcy + (wr - 7) * u[1])
base = (dial_cx + (wr + 9) * u[0], wcy + (wr + 9) * u[1])
bl = (base[0] + 5 * v[0], base[1] + 5 * v[1])
br = (base[0] - 5 * v[0], base[1] - 5 * v[1])
d.polygon([tip, bl, br], fill=BLACK)
d.text((dial_cx, wcy), "12", font=f_mph, fill=BLACK, anchor="mm")

# ---- Bottom ticks ----
for bx in (156, round(divider_x), 590, 658, 726):
    d.line((bx, 88, bx, 132), fill=BLACK)

# ---- 7-day forecast strip ----
line_y = 214
gx0, gx1 = 8, 784
d.line((gx0, line_y, gx1, line_y), fill=BLACK)
colw = (gx1 - gx0) / 7
for i in range(1, 7):
    sx = gx0 + i * colw
    d.line((sx, line_y, sx, line_y + 29), fill=BLACK)
days  = ["THU", "FRI", "SAT", "SUN", "MON", "TUE", "WED"]
codes = ["\uF013", "\uF019", "\uF013", "\uF013", "\uF019", "\uF019", "\uF019"]
hi    = ["73", "76", "80", "76", "78", "58", "60"]
lo    = ["49", "56", "60", "58", "61", "46", "43"]
for i in range(7):
    x0 = gx0 + i * colw
    d.text((x0 + 8, line_y), codes[i], font=f_ficon, fill=BLACK, anchor="la")
    d.text((x0 + 58, line_y + 2), days[i], font=f_fday, fill=BLACK, anchor="la")
    cx = x0 + 83
    d.text((cx, line_y + 21), hi[i] + "\u00B0", font=f_fhi, fill=BLACK, anchor="ma")
    d.text((cx, line_y + 40), lo[i] + "\u00B0", font=f_flo, fill=BLACK, anchor="ma")

out = "/home/sharby/repos/weather-paper/preview/wind_dial.png"
img.save(out)
print("saved; temp_f_right=%.1f divider=%.1f dial_cx=%.1f temp_top_y=%.1f" % (temp_f_right, divider_x, dial_cx, temp_top_y))
