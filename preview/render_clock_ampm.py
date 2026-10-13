from PIL import Image, ImageDraw, ImageFont
import base64

W, H = 792, 272
img = Image.new("1", (W, H), 1)
d = ImageDraw.Draw(img)
FD = "/home/sharby/repos/weather-paper/esphome/fonts/"
def F(n, s): return ImageFont.truetype(FD + n, s)

f_clock = F("DejaVuSans-Bold.ttf", 80)
f_ampm  = F("DejaVuSans-Bold.ttf", 22)

d.line((0, 88, W, 88), fill=0)
d.line((308, 44, 308, 88), fill=0)  # clock/calendar tick

cbuf = "12:45"
d.text((16, -7), cbuf, font=f_clock, fill=0, anchor="la")
aw = d.textlength(cbuf, font=f_clock)
apx = 16 + aw + 8
d.text((apx, 14), "P", font=f_ampm, fill=0, anchor="la")
d.text((apx, 40), "M", font=f_ampm, fill=0, anchor="la")

img2 = img.resize((W * 2, H * 2), Image.NEAREST)
img2.save("/home/sharby/repos/weather-paper/preview/clock_ampm.png")
b64 = base64.b64encode(open("/home/sharby/repos/weather-paper/preview/clock_ampm.png","rb").read()).decode()
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:transparent;}}img{{image-rendering:pixelated;width:100%;max-width:792px;display:block;}}</style>
</head><body><img src="data:image/png;base64,{b64}"></body></html>"""
open("/home/sharby/repos/weather-paper/preview/clock_ampm.html","w").write(html)
print("saved clock_ampm.png + clock_ampm.html")
