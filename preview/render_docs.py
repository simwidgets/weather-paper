"""Generate documentation screenshots for the Weather Paper GitHub Pages site.

Renders each screen at the native 792x272 (1-bit, like the e-paper) using the
same fonts/geometry as the firmware display lambda.
"""
from PIL import Image, ImageDraw, ImageFont
import math, os

W, H = 792, 272
FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
OUT = "/home/sharby/repos/weather-paper/docs/images/"

def F(name, size):
    return ImageFont.truetype(FD + name, size)

# --- shared fonts ----------------------------------------------------------
f_clock  = F("DejaVuSans-Bold.ttf", 90)
f_day    = F("DejaVuSans-Bold.ttf", 22)
f_month  = F("DejaVuSans-Bold.ttf", 18)
f_small  = F("DejaVuSans.ttf", 14)
f_icon   = F("weathericons.ttf", 90)
f_icon_b = F("weathericons.ttf", 145)
f_temp   = F("DejaVuSans-Bold.ttf", 132)
f_unit   = F("DejaVuSans-Bold.ttf", 42)
f_meas   = F("DejaVuSans.ttf", 16)
f_label  = F("DejaVuSans-Bold.ttf", 13)
f_cal_h  = F("DejaVuSans-Bold.ttf", 11)
f_wx     = F("DejaVuSans.ttf", 12)
f_zip    = F("DejaVuSans-Bold.ttf", 18)
f_sta    = F("DejaVuSans-Bold.ttf", 14)
f_src    = F("mdi.ttf", 20)
f_card   = F("DejaVuSans-Bold.ttf", 16)
f_mph    = F("DejaVuSans-Bold.ttf", 30)
f_ficon  = F("weathericons.ttf", 48)
f_fday   = F("DejaVuSans-Bold.ttf", 12)
f_fhi    = F("DejaVuSans-Bold.ttf", 14)
f_flo    = F("DejaVuSans.ttf", 11)
f_title  = F("DejaVuSans-Bold.ttf", 36)
f_set    = F("DejaVuSans-Bold.ttf", 20)

BLACK = 0


def new():
    img = Image.new("1", (W, H), 1)
    return img, ImageDraw.Draw(img)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    img.save(p)
    print("saved", p)


# ============================== MAIN ======================================
def main():
    img, d = new()
    band_mid = (88 + 214) / 2

    d.line((0, 88, W, 88), fill=BLACK)

    # clock
    d.text((16, -7), "10:45", font=f_clock, fill=BLACK)
    # date (Sunday / October 11)
    d.text((580, 14), "Sunday", font=f_day, fill=BLACK, anchor="ma")
    d.text((580, 48), "October 11", font=f_month, fill=BLACK, anchor="ma")

    # status stack (WiFi mode, no Ruuvi)
    d.text((772, 10), "RSSI -68dBm", font=f_small, fill=BLACK, anchor="ra")
    d.text((772, 30), "--", font=f_small, fill=BLACK, anchor="ra")
    d.text((772, 54), "--", font=f_small, fill=BLACK, anchor="ra")
    d.text((772, 70), "WiFi 60s", font=f_small, fill=BLACK, anchor="ra")
    d.text((668, 26), "WX: 10/11 @ 10:30", font=f_wx, fill=BLACK, anchor="la")
    d.text((668, 46), "90210", font=f_zip, fill=BLACK, anchor="la")
    d.text((791, 46), "KSMO", font=f_sta, fill=BLACK, anchor="ra")
    d.text((668, 66), "\U000F05A9", font=f_src, fill=BLACK, anchor="la")

    # calendar — October 2026, Oct 1 = Thursday (offset 3)
    cx0, cx1 = 314, 496
    cy0, cy1 = 6, 86
    cw = (cx1 - cx0) / 7
    rh = (cy1 - cy0) / 6
    for i, ch in enumerate("SMTWTFS"):
        d.text((cx0 + cw/2 + i*cw, cy0 - 1), ch, font=f_cal_h, fill=BLACK, anchor="ma")
    for w in range(5):
        for c in range(7):
            day = w*7 + c - 3          # Oct 1 (Thu) => day 1
            if day < 1 or day > 31:
                continue
            x0 = cx0 + c*cw
            y0 = cy0 + (w+1)*rh
            if day == 11:              # today (Sun Oct 11)
                d.rectangle((x0+1, y0+1, x0+cw-1, y0+rh-1), fill=BLACK)
            else:
                d.rectangle((x0+1, y0+1, x0+cw-1, y0+rh-1), outline=BLACK)
    for tx in (308, 505, 664):
        d.line((tx, 44, tx, 88), fill=BLACK)

    # weather icon (cloudy) centered in band + PoP in the top-left corner
    icon_bbox = d.textbbox((0, 0), "\uF013", font=f_icon)
    icon_x = 72 - (icon_bbox[0] + icon_bbox[2]) / 2
    icon_y = band_mid - (icon_bbox[1] + icon_bbox[3]) / 2
    d.text((icon_x, icon_y), "\uF013", font=f_icon, fill=BLACK, anchor="la")
    d.text((1, 88), "78%", font=f_sta, fill=BLACK, anchor="la")

    # temperature 70 F, degF pinned to the divider (y=88) top-right
    num = "70"
    nw = d.textlength(num, font=f_temp)
    uw = d.textlength("\u00B0F", font=f_unit)
    temp_cx = 270
    temp_f_right = temp_cx + nw/2 + 4 + uw
    bbox = d.textbbox((0, 0), num, font=f_temp)
    temp_top_y = band_mid - (bbox[1] + bbox[3]) / 2
    d.text((temp_cx - nw/2, temp_top_y), num, font=f_temp, fill=BLACK, anchor="la")
    d.text((temp_cx + nw/2 + 4, 88), "\u00B0F", font=f_unit, fill=BLACK, anchor="la")

    # bars
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

    bar(556, "HMD", 69, 0, 100, "69%")
    bar(624, "PRS", 29.66, 28.0, 32.0, "29.66 in")
    bar(692, "DPT", 59, -20, 100, "59\u00B0F")
    bar(760, "FEEL", 70, -70, 135, "70\u00B0F")

    # wind dial (with 32 little ticks every 10 deg + 4 thick cardinal wedges)
    wr = 38
    d_lab = 10
    bar_tick_x = (556 - bar_w//2) - 7
    w_hw = d.textlength("W", font=f_card) / 2
    dial_cx = (temp_f_right - wr - d_lab - w_hw + 2*bar_tick_x) / 3
    W_left = dial_cx - wr - d_lab - w_hw
    divider_x = (temp_f_right + W_left) / 2
    wcy = band_mid
    d.ellipse((dial_cx-wr, wcy-wr, dial_cx+wr, wcy+wr), outline=BLACK)

    # thick cardinal wedges (N/E/S/W): tip inward at r=27, base at the stroke r=36
    def wtick(deg, length, hw):
        ar = math.radians(deg)
        su, cu = math.sin(ar), math.cos(ar)
        tip = (dial_cx + (wr - 2 - length) * su, wcy - (wr - 2 - length) * cu)
        bcx = dial_cx + (wr - 2) * su
        bcy = wcy - (wr - 2) * cu
        bl = (bcx + hw * cu, bcy + hw * su)
        br = (bcx - hw * cu, bcy - hw * su)
        d.polygon([tip, bl, br], fill=BLACK)

    for a in (0, 90, 180, 270):
        wtick(a, 9, 2)

    # 32 little ticks every 10 deg (skipping the cardinals a%9==0)
    for a in range(36):
        if a % 9 == 0:
            continue
        ar = a * math.pi / 18.0
        su, cu = math.sin(ar), math.cos(ar)
        d.line((dial_cx + (wr - 2) * su, wcy - (wr - 2) * cu,
                dial_cx + (wr - 6) * su, wcy - (wr - 6) * cu), fill=BLACK)

    d.text((dial_cx, wcy - wr - 11), "N", font=f_card, fill=BLACK, anchor="mm")
    d.text((dial_cx, wcy + wr + 11), "S", font=f_card, fill=BLACK, anchor="mm")
    d.text((dial_cx + wr + 11, wcy), "E", font=f_card, fill=BLACK, anchor="mm")
    d.text((dial_cx - wr - 11, wcy), "W", font=f_card, fill=BLACK, anchor="mm")

    # wind direction tick (pointing inward) at 210 deg, 8 MPH
    deg = 210
    rad = math.radians(deg)
    u = (math.sin(rad), -math.cos(rad))   # outward radial
    v = (math.cos(rad), math.sin(rad))    # perpendicular
    tip = (dial_cx + (wr - 7) * u[0], wcy + (wr - 7) * u[1])
    base = (dial_cx + (wr + 9) * u[0], wcy + (wr + 9) * u[1])
    d.polygon([tip, (base[0] + 5*v[0], base[1] + 5*v[1]),
               (base[0] - 5*v[0], base[1] - 5*v[1])], fill=BLACK)
    d.text((dial_cx, wcy), "8", font=f_mph, fill=BLACK, anchor="mm")

    for bx in (156, round(divider_x), 590, 658, 726):
        d.line((bx, 88, bx, 132), fill=BLACK)

    # 7-day forecast strip (real NWS 90210 data for 2026-10-11)
    line_y = 214
    gx0, gx1 = 8, 784
    d.line((gx0, line_y, gx1, line_y), fill=BLACK)
    colw = (gx1 - gx0) / 7
    for i in range(1, 7):
        sx = gx0 + i * colw
        d.line((sx, line_y, sx, line_y + 29), fill=BLACK)
    days  = ["TODAY", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    codes = ["\uF019", "\uF019", "\uF00D", "\uF00D", "\uF00D", "\uF00D", "\uF00D"]
    pcodes = [51, 51, 0, 0, 0, 0, 0]
    ppct  = [78, 70, 0, 0, 0, 0, 0]
    hi = ["70", "66", "72", "75", "83", "88", "88"]
    lo = ["57", "53", "55", "59", "66", "69", "67"]
    for i in range(7):
        x0 = gx0 + i * colw
        d.text((x0 + 8, line_y), codes[i], font=f_ficon, fill=BLACK, anchor="la")
        # precipitation chance on rain/snow/thunder days
        if pcodes[i] in (51, 71, 95) and ppct[i] > 0:
            d.text((x0 + 2, line_y + 2), f"{ppct[i]}%", font=f_flo, fill=BLACK, anchor="la")
        d.text((x0 + 58, line_y + 2), days[i], font=f_fday, fill=BLACK, anchor="la")
        cx = x0 + 83
        d.text((cx, line_y + 21), hi[i] + "\u00B0", font=f_fhi, fill=BLACK, anchor="ma")
        d.text((cx, line_y + 40), lo[i] + "\u00B0", font=f_flo, fill=BLACK, anchor="ma")

    save(img, "main.png")


# ============================== SETUP =====================================
def setup():
    img, d = new()
    d.text((396, 18), "WiFi SETUP", font=f_title, fill=BLACK, anchor="ma")
    d.text((396, 58), "1. Connect your phone to:", font=f_small, fill=BLACK, anchor="ma")
    d.text((396, 74), "WeatherPaper-1A2B3C", font=f_set, fill=BLACK, anchor="ma")
    qr = Image.open("/home/sharby/repos/weather-paper/esphome/setup_qr.png").convert("1")
    img.paste(qr, (330, 100))
    d.text((396, 238), "2. Scan the QR code", font=f_small, fill=BLACK, anchor="ma")
    d.text((396, 254), "(or open a browser to 192.168.4.1)", font=f_small, fill=BLACK, anchor="ma")
    save(img, "setup.png")


# ============================ CONNECTING ==================================
def connecting():
    img, d = new()
    d.text((396, 60), "Connecting to WiFi", font=f_title, fill=BLACK, anchor="ma")
    d.text((396, 130), "HomeNetwork", font=f_set, fill=BLACK, anchor="ma")
    d.text((396, 170), "Loading...", font=f_small, fill=BLACK, anchor="ma")
    d.text((396, 200), "May take a couple minutes", font=f_small, fill=BLACK, anchor="ma")
    save(img, "connecting.png")


# ============================ LOADING =====================================
def loading():
    img, d = new()
    lic = "\uF041"  # partly cloudy (representative of the random pick)
    bb = d.textbbox((0, 0), lic, font=f_icon_b)
    d.text((396 - (bb[0] + bb[2]) / 2, 92 - (bb[1] + bb[3]) / 2),
           lic, font=f_icon_b, fill=BLACK, anchor="la")
    d.text((396, 185), "Loading Weather", font=f_title, fill=BLACK, anchor="ma")
    d.text((396, 228), "This may take ~25 seconds", font=f_small, fill=BLACK, anchor="ma")
    save(img, "loading.png")


# ============================ SETTINGS ====================================
def settings():
    img, d = new()
    d.text((396, 8), "SETTINGS", font=f_title, fill=BLACK, anchor="ma")
    labels = ["WiFi", "Weather", "Ruuvi", "Temperature", "Pressure",
              "Time Format", "Screen Refresh", "Update", "Factory Reset"]
    values = ["ON", "WiFi", "OFF", "\u00B0F", "inHg", "AM/PM", "Partial", "1hr", ">"]
    sel = 1  # Weather selected
    for i in range(9):
        y = 50 + i * 23
        if i == sel:
            d.text((56, y), "\u25B6", font=f_set, fill=BLACK, anchor="la")
        d.text((104, y), labels[i], font=f_set, fill=BLACK, anchor="la")
        d.text((740, y), values[i], font=f_set, fill=BLACK, anchor="ra")
    save(img, "settings.png")


if __name__ == "__main__":
    main()
    setup()
    connecting()
    loading()
    settings()
    print("done")
