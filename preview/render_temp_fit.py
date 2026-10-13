from PIL import Image, ImageDraw, ImageFont

W, H = 792, 214  # bottom section (divider 88 -> forecast line 214)
FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
def F(name, size):
    return ImageFont.truetype(FD + name, size)

f_big  = F("DejaVuSans-Bold.ttf", 132)
f_sml  = F("DejaVuSans-Bold.ttf", 88)
f_unit = F("DejaVuSans-Bold.ttf", 42)
f_icon = F("weathericons.ttf", 90)
f_label= F("DejaVuSans-Bold.ttf", 13)
f_meas = F("DejaVuSans.ttf", 16)
f_ficon= F("weathericons.ttf", 48)
f_fday = F("DejaVuSans-Bold.ttf", 12)
f_fhi  = F("DejaVuSans-Bold.ttf", 14)
f_flo  = F("DejaVuSans.ttf", 11)

cases = [("79", 79), ("-10", -10), ("105", 105)]

# stack 3 rows + a 4px gap between each
gap = 6
rows = len(cases)
img = Image.new("1", (W, rows * H + (rows - 1) * gap), 1)
d = ImageDraw.Draw(img)

def draw_row(yoff, num, tdeg):
    # horizontal lines
    d.line((0, yoff + 0, W, yoff + 0), fill=0)          # divider (88 -> 0 offset)
    d.line((0, yoff + 126, W, yoff + 126), fill=0)      # forecast line (214 -> 126 offset)

    # weather icon (centered at x=72, ascender at yoff+... mirrors 86-> -2 offset)
    d.text((72, yoff - 2), "\uF00D", font=f_icon, fill=0, anchor="ma")

    # temp auto-size + center vertically (digit bbox center at 151 -> yoff+63)
    big = (tdeg >= 0 and tdeg < 100)
    f = f_big if big else f_sml
    bbox = d.textbbox((0, 0), num, font=f)
    dh = bbox[3] - bbox[1]
    dc = bbox[1] + dh / 2
    ty = yoff + 63 - int(dc)   # center digit bbox at yoff+63 (=151)
    nw = d.textlength(num, font=f)
    d.text((270, ty), num, font=f, fill=0, anchor="ma")
    d.text((270 + nw / 2 + 4, yoff + 8), "\u00B0F", font=f_unit, fill=0, anchor="la")

    # bars (HMD/PRS/DPT/TMP) with labels, to show the fit boundary
    for cx, lab in ((445, "HMD"), (545, "PRS"), (645, "DPT"), (745, "TMP")):
        d.text((cx, yoff + 2), lab, font=f_label, fill=0, anchor="ma")
        d.rectangle((cx - 26, yoff + 16, cx + 26, yoff + 98), outline=0)
        d.rectangle((cx - 22, yoff + 60, cx + 22, yoff + 94), fill=0)
    # HMD bar's left edge marker (the temp+degF must not cross x=419)
    d.line((419, yoff + 12, 419, yoff + 102), fill=0)

    # label the case
    d.text((30, yoff + 140), f"case: {num}", font=f_fhi, fill=0, anchor="la")

for i, (num, tdeg) in enumerate(cases):
    draw_row(i * (H + gap), num, tdeg)

img.save("/home/sharby/repos/weather-paper/preview/temp_fit.png")
print("saved", img.size)
