from PIL import Image, ImageDraw, ImageFont
import base64

W, H = 792, 272
img = Image.new("1", (W, H), 1)
d = ImageDraw.Draw(img)
FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
def F(n, s): return ImageFont.truetype(FD + n, s)

f_temp = F("DejaVuSans-Bold.ttf", 132)
f_unit = F("DejaVuSans-Bold.ttf", 42)
f_small = F("DejaVuSans.ttf", 14)

# context lines
d.line((0, 88, W, 88), fill=0)          # divider
d.line((8, 214, 784, 214), fill=0)      # forecast line

# big temp (device: TOP_LEFT at (270 - tw/2, temp_y), temp_y = 151 - th/2)
num = "75"
nw = d.textlength(num, font=f_temp)
t_asc, t_desc = f_temp.getmetrics()
temp_y = 151 - (t_asc + t_desc) // 2
d.text((270 - nw / 2, temp_y), num, font=f_temp, fill=0, anchor="la")

# °F superscript (device: TOP_LEFT at (270 + tw/2 + 4, 96))
unit = "\u00B0F"
uw = d.textlength(unit, font=f_unit)
unit_x = 270 + nw / 2 + 4
d.text((unit_x, 96), unit, font=f_unit, fill=0, anchor="la")

# big number baseline
big_baseline = temp_y + t_asc

# Ruuvi reference (device: right edge = °F right edge, baseline = big baseline)
r = "73\u00B0F"
rw = d.textlength(r, font=f_small)
right_edge = unit_x + uw
d.text((right_edge - rw, big_baseline), r, font=f_small, fill=0, anchor="ls")

# upscale 3x for the preview frame
img3 = img.resize((W * 3, H * 3), Image.NEAREST)
img3.save("/home/sharby/repos/weather-paper/preview/ruuvi_ref.png")

b64 = base64.b64encode(open("/home/sharby/repos/weather-paper/preview/ruuvi_ref.png", "rb").read()).decode()
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:transparent;}}
img{{image-rendering:pixelated;width:100%;max-width:792px;display:block;}}
</style></head><body><img src="data:image/png;base64,{b64}"></body></html>"""
open("/home/sharby/repos/weather-paper/preview/ruuvi_ref.html", "w").write(html)
print("saved ruuvi_ref.png + ruuvi_ref.html")
