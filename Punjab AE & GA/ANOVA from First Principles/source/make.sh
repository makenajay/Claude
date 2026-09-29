set -e
python3 compute.py 2>&1 | grep -iv "findfont" | tail -0
python3 build.py
NPM_ROOT=$(npm root -g) CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome node render.js 2>&1 | grep -v agent-proxy | head -3
python3 merge.py
python3 -c "
import pymupdf
d=pymupdf.open('build/ANOVA.pdf')
W,Hh=595*0.5,842*0.5
for s in range(0,len(d),8):
    out=pymupdf.open(); pg=out.new_page(width=W*4,height=Hh*2)
    for j,i in enumerate(range(s,min(s+8,len(d)))):
        r=pymupdf.Rect((j%4)*W,(j//4)*Hh,(j%4+1)*W,(j//4+1)*Hh); pg.show_pdf_page(r,d,i); pg.draw_rect(r,color=(.7,.7,.7),width=.5)
    pg.get_pixmap(dpi=110).save(f'pages/sheet{s//8+1}.png')
"
