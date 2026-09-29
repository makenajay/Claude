"""Fill content.html placeholders [[python-expr|fmt]] with verified results -> build/body.html"""
import json, os, re, html, shutil
H = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(H, "build")
R = json.load(open(os.path.join(B, "results.json")))
O = R["oneway"]; reg = R["reg"]; tw_add, tw_int = R["tw_add"], R["tw_int"]
psu, pun, cost, sim, tukey = R["psu"], R["punjab"], R["cost"], R["sim"], R["tukey"]

# fonts
F = os.path.join(H, "node_modules/@fontsource"); os.makedirs(os.path.join(B, "fonts"), exist_ok=True)
for src, dst in [("source-serif-4/files/source-serif-4-latin-400-normal.woff2", "ss4-400"), ("source-serif-4/files/source-serif-4-latin-400-italic.woff2", "ss4-400i"),
                 ("source-serif-4/files/source-serif-4-latin-600-normal.woff2", "ss4-600"), ("source-serif-4/files/source-serif-4-latin-700-normal.woff2", "ss4-700"),
                 ("fraunces/files/fraunces-latin-600-normal.woff2", "fr-600"), ("fraunces/files/fraunces-latin-800-normal.woff2", "fr-800"),
                 ("jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2", "jb-400"), ("jetbrains-mono/files/jetbrains-mono-latin-700-normal.woff2", "jb-700")]:
    shutil.copy(os.path.join(F, src), os.path.join(B, "fonts", dst + ".woff2"))
shutil.copy(os.path.join(H, "style.css"), B)

def pf(p):
    return "&lt; 0.001" if p < 0.001 else f"{p:.3f}"

def n2(x, d=2):
    return f"{x:,.{d}f}"

ICONS = {
 "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
 "alert": '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>',
 "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 "code": '<path d="m8 8-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
 "q": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17h.01"/>',
 "fix": '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="m13.5 6.5 4 4"/>',
 "proof": '<path d="M5 12l4 4L19 6"/>',
}
def icon(n):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[n]}</svg>'

def call(kind, tag, ic):
    return f'<div class="callout {kind}"><div class="tag">{icon(ic)}{tag}</div>'

def anova_table(k, label="groups"):
    o = O[k]
    return f"""<table class="tight"><tr><th>Source</th><th class="r">SS</th><th class="r">df</th><th class="r">MS</th><th class="r">F</th><th class="r">p</th></tr>
<tr><td><span class="sw" style="background:var(--sig)"></span>Between {label}</td><td class="r">{n2(o['ssb'])}</td><td class="r">{o['dfb']}</td><td class="r">{n2(o['msb'])}</td><td class="r">{n2(o['F'])}</td><td class="r">{pf(o['p'])}</td></tr>
<tr><td><span class="sw" style="background:var(--noi)"></span>Within {label}</td><td class="r">{n2(o['ssw'])}</td><td class="r">{o['dfw']}</td><td class="r">{n2(o['msw'], 3 if o['msw'] < 0.1 else 2)}</td><td></td><td></td></tr>
<tr class="tot"><td><span class="sw" style="background:var(--tot)"></span>Total</td><td class="r">{n2(o['sst'])}</td><td class="r">{o['n']-1}</td><td></td><td></td><td></td></tr></table>"""

def tw_table(tw):
    rows = "".join(
        f"<tr><td>{r['src']}</td><td class='r'>{n2(r['ss'])}</td><td class='r'>{r['df']}</td><td class='r'>{n2(r['ms']) if 'ms' in r else ''}</td>"
        f"<td class='r'>{n2(r['F']) if 'F' in r else ''}</td><td class='r'>{pf(r['p']) if 'p' in r else ''}</td></tr>" for r in tw["rows"][:-1])
    t = tw["rows"][-1]
    return (f"<table class='tight'><tr><th>Source</th><th class='r'>SS</th><th class='r'>df</th><th class='r'>MS</th><th class='r'>F</th><th class='r'>p</th></tr>{rows}"
            f"<tr class='tot'><td>Total</td><td class='r'>{n2(t['ss'])}</td><td class='r'>{t['df']}</td><td></td><td></td><td></td></tr></table>")

def tw_both():
    head = ("<table class='tight'><tr><th rowspan=2>Source</th><th class='r' rowspan=2>df</th><th class='r' colspan=3 style='text-align:center'>Scenario 1: parallel lines</th>"
            "<th class='r' colspan=3 style='text-align:center'>Scenario 2: crossing lines</th></tr><tr>" + "<th class='r'>SS</th><th class='r'>F</th><th class='r'>p</th>" * 2 + "</tr>")
    rows = []
    for i, (a, b) in enumerate(zip(tw_add["rows"], tw_int["rows"])):
        cls = " class='tot'" if a["src"] == "Total" else (" class='hl'" if "×" in a["src"] else "")
        cell = lambda r: f"<td class='r'>{n2(r['ss'])}</td><td class='r'>{n2(r['F']) if 'F' in r else ''}</td><td class='r'>{pf(r['p']) if 'p' in r else ''}</td>"
        rows.append(f"<tr{cls}><td>{a['src']}</td><td class='r'>{a['df']}</td>{cell(a)}{cell(b)}</tr>")
    return head + "".join(rows) + "</table><p class='small muted'>MS<sub>residual</sub> = 18/18 = 1.00 in both scenarios, so each F equals its MS.</p>"

def results_table():
    out = ["<table class='tight'><tr><th>#</th><th>Application</th><th class='r'>Total var</th><th class='r'>MS<sub>within</sub></th><th class='r'>F</th><th class='r'>p</th><th class='r'>η²</th><th class='r'>ω²</th></tr>"]
    for i, k in enumerate(O, 1):
        o = O[k]; cls = " class='hl'" if k in ("batt", "courier") else ""
        t = o["title"].split("  (")[0]
        out.append(f"<tr{cls}><td>{i}</td><td>{t}</td><td class='r'>{n2(o['totvar'])}</td><td class='r'>{n2(o['msw'], 3 if o['msw'] < .1 else 2)}</td>"
                   f"<td class='r'>{n2(o['F'])}</td><td class='r'>{pf(o['p'])}</td><td class='r'>{o['eta']:.3f}</td><td class='r'>{max(o['omega'],0):.3f}</td></tr>")
    return "".join(out) + "</table>"

def data_table():
    out = ["<table class='tight small'><tr><th>#</th><th>Application</th><th>Groups and toy observations  (group mean)</th></tr>"]
    for i, k in enumerate(O, 1):
        o = O[k]; cls = " class='hl'" if k in ("batt", "courier") else ""
        g = "<br>".join(f"<b>{nm}</b>: {', '.join(f'{v:g}' for v in d)} <span class='muted'>({m:.2f})</span>" for nm, d, m in zip(o["names"], o["data"], o["means"]))
        out.append(f"<tr{cls}><td>{i}</td><td>{o['title'].split('  (')[0]}<br><span class='muted small'>unit: {o['unit']}</span></td><td>{g}</td></tr>")
    return "".join(out) + "</table>"

BUDGET = 200 * 6000 + 2400 * 300   # cost of the 200 x 12 design
def design_rows(rho=0.06, c1=6000, c2=300):
    out = []
    best = None
    for m in (4, 8, 12, 18, 30, 50):
        k = int(BUDGET // (c1 + c2 * m)); n = k * m; d = 1 + (m - 1) * rho; ne = n / d
        out.append((m, k, n, d, ne))
    top = max(r[4] for r in out)
    rows = "".join(
        f"<tr{' class=hl' if r[4] == top else ''}><td class='r'>{r[0]}</td><td class='r'>{r[1]}</td><td class='r'>{r[2]:,}</td>"
        f"<td class='r'>{r[3]:.2f}</td><td class='r'><b>{r[4]:,.0f}</b></td><td class='r'>±{100*1.96*(0.35*0.65*r[3]/r[2])**0.5:.2f}</td></tr>" for r in out)
    return ("<table class='tight'><tr><th class='r'>Interviews per booth (m)</th><th class='r'>Booths affordable</th><th class='r'>Total interviews n</th>"
            "<th class='r'>DEFF</th><th class='r'>Effective n</th><th class='r'>MOE for 35% (pts)</th></tr>" + rows + "</table>")

def rcode(txt, label="R"):
    s = html.escape(txt.strip("\n"))
    toks = re.compile(r'(#[^\n]*)|("[^"\n]*")|\b(function|library|if|else|for|TRUE|FALSE)\b|\b([A-Za-z_.][A-Za-z0-9_.]*)(?=\()|(?<![\w.])(\d+\.?\d*(?:e-?\d+)?)')
    def rep(m):
        if m.group(1): return f'<span class="c">{m.group(1)}</span>'
        if m.group(2): return f'<span class="s">{m.group(2)}</span>'
        if m.group(3): return f'<span class="k">{m.group(3)}</span>'
        if m.group(4): return f'<span class="f">{m.group(4)}</span>'
        return f'<span class="n">{m.group(5)}</span>'
    s = toks.sub(rep, s.replace("&quot;", '"'))
    return f'<pre class="r"><span class="lab">{label}</span>{s}</pre>'

def out(txt):
    return f'<pre class="out">{html.escape(txt.strip(chr(10)))}</pre>'

def fig(name, cap):
    return f'<figure><img src="fig/{name}.svg"><figcaption>{cap}</figcaption></figure>'

import glob
src = "\n".join(open(p).read() for p in sorted(glob.glob(os.path.join(H, "content[0-9].html"))))
# multi-line blocks: [[R ... R]] and [[OUT ... OUT]]
blocks = []
def stash(h):
    blocks.append(h); return f"\x00{len(blocks)-1}\x00"
src = re.sub(r"\[\[R\n(.*?)\nR\]\]", lambda m: stash(rcode(m.group(1))), src, flags=re.S)
src = re.sub(r"\[\[OUT\n(.*?)\nOUT\]\]", lambda m: stash(out(m.group(1))), src, flags=re.S)
def sub(m):
    expr, _, fmt = m.group(1).partition("|")
    v = eval(expr)
    return format(v, fmt) if fmt else str(v)
pat = re.compile(r"\[\[((?:(?!\[\[).)+?)\]\](?!\])", re.S)
while pat.search(src):
    src = pat.sub(sub, src)
src = re.sub(r"\x00(\d+)\x00", lambda m: blocks[int(m.group(1))], src)
open(os.path.join(B, "body.html"), "w").write(src)
print("ok", len(src))
