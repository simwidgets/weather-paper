from PIL import Image, ImageDraw, ImageFont

W, H = 792, 272
img = Image.new("1", (W, H), 1)  # 1 = white
d = ImageDraw.Draw(img)

FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
def F(name, size):
    return ImageFont.truetype(FD + name, size)

f_icon  = F("weathericons.ttf", 145)
f_temp  = F("DejaVuSans-Bold.ttf", 150)
f_unit  = F("DejaVuSans-Bold.ttf", 44)
f_small = F("DejaVuSans.ttf", 14)
f_meas  = F("DejaVuSans.ttf", 16)
f_label = F("DejaVuSans-Bold.ttf", 13)
f_graph = F("DejaVuSans.ttf", 9)

BLACK = 0
WHITE = 1

# ---- Weather icon (much bigger) ----
d.text((76, 6), "\uF00D", font=f_icon, fill=BLACK, anchor="ma")

# ---- Temperature (3-digit worst case: 104, unit pulled in) ----
num = "75"
nw = d.textlength(num, font=f_temp)
temp_cx = 286
d.text((temp_cx, 26), num, font=f_temp, fill=BLACK, anchor="ma")
d.text((temp_cx + nw / 2 - 6, 26), "\u00B0F", font=f_unit, fill=BLACK, anchor="la")

# ---- Four bar meters (all skinny) ----
def bar(cx, lab, val, vmin, vmax, v1, v2):
    w = 40
    hw = w // 2
    x0, x1, top, bot, wb = cx - hw, cx + hw, 55, 185, 4
    d.text((cx, 41), lab, font=f_label, fill=BLACK, anchor="ma")
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
        d.text((cx, 192), v1, font=f_meas, fill=BLACK, anchor="ma")

bar(482, "HMD", 42, 0, 100, "42%", None)
bar(545, "PRS", 29.97, 28.0, 32.0, "29.97", "inHg")
bar(605, "DPT", 48, -20, 100, "48\u00B0F", None)
bar(665, "TMP", 75, -40, 120, "75\u00B0F", None)

# ---- Ruuvi status (right of last bar) ----
d.text((792, 85), "RSSI -68dBm", font=f_small, fill=BLACK, anchor="ra")

batt_v = 2.94
bf = max(0.0, min(1.0, (batt_v - 2.0) / (3.0 - 2.0)))
bb_w, bb_h = 44, 13
bbx0 = 792 - 2 - bb_w
bby = 107
d.rectangle((bbx0, bby, bbx0 + bb_w - 1, bby + bb_h - 1), outline=BLACK)
d.rectangle((bbx0 + bb_w, bby + 3, bbx0 + bb_w + 2, bby + bb_h - 4), outline=BLACK)
fill_w = round((bb_w - 4) * bf)
d.rectangle((bbx0 + 2, bby + 2, bbx0 + 2 + fill_w - 1, bby + bb_h - 3), fill=BLACK)
d.text((bbx0 - 6, bby), "2.94V", font=f_small, fill=BLACK, anchor="ra")

d.text((792, 131), "Move 137", font=f_small, fill=BLACK, anchor="ra")

# ---- 14-day pressure graph (bottom) ----
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

img.save("/home/sharby/repos/weather-paper/preview/offline.png")
print("saved")
