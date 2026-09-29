"""Recompute every statistic in the chapter and draw all figures as SVG."""
import json, os
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), "build")
os.makedirs(os.path.join(OUT, "fig"), exist_ok=True)

INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
MAGENTA, RED, YELLOW = "#e87ba4", "#e34948", "#eda100"
GROUP = [BLUE, ORANGE, AQUA, VIOLET]
SIGNAL, NOISE, TOTAL = ORANGE, BLUE, VIOLET

plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "Inter", "font.size": 9,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 10, "axes.titleweight": "semibold", "axes.titlelocation": "left",
    "axes.titlepad": 8, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False,
    "figure.facecolor": "none", "axes.facecolor": "none", "lines.linewidth": 2,
})

def save(fig, name):
    fig.savefig(os.path.join(OUT, "fig", name + ".svg"), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)

R = {}  # results for the document

# ----------------------------------------------------------------- one-way
def oneway(groups):
    ys = [np.asarray(v, float) for v in groups.values()]
    a = np.concatenate(ys); n, k = len(a), len(ys); gm = a.mean()
    sst = ((a - gm) ** 2).sum()
    ssw = sum(((y - y.mean()) ** 2).sum() for y in ys); ssb = sst - ssw
    dfb, dfw = k - 1, n - k; msb, msw = ssb / dfb, ssw / dfw; F = msb / msw
    # Welch
    ni = np.array([len(y) for y in ys]); mi = np.array([y.mean() for y in ys])
    vi = np.array([y.var(ddof=1) for y in ys]); w = ni / vi; mw = (w * mi).sum() / w.sum()
    lam = ((1 - w / w.sum()) ** 2 / (ni - 1)).sum()
    Fw = ((w * (mi - mw) ** 2).sum() / (k - 1)) / (1 + 2 * (k - 2) / (k ** 2 - 1) * lam)
    dfw2 = (k ** 2 - 1) / (3 * lam)
    return dict(names=list(groups), data=[list(map(float, y)) for y in ys],
                means=mi.tolist(), vars=vi.tolist(), n=n, k=k, gm=gm,
                sst=sst, ssb=ssb, ssw=ssw, dfb=dfb, dfw=dfw, msb=msb, msw=msw, F=F,
                p=stats.f.sf(F, dfb, dfw), eta=ssb / sst, omega=(ssb - dfb * msw) / (sst + msw),
                totvar=sst / (n - 1), Fcrit=stats.f.ppf(.95, dfb, dfw),
                welchF=Fw, welchdf=dfw2, welchp=stats.f.sf(Fw, k - 1, dfw2))

EX = [
 ("fert", "Fertilizer type → wheat yield", "q/acre", {"A": [18,20,19,21,22], "B": [23,25,24,26,25], "C": [20,21,22,19,20]}),
 ("teach", "Teaching method → exam score", "score", {"Lecture": [62,65,68,64,66], "Hybrid": [70,74,72,71,75], "Workshop": [77,80,78,82,79]}),
 ("bolt", "Machine → bolt tensile strength", "strength", {"M1": [101,99,100,102,98], "M2": [105,106,104,107,105], "M3": [100,101,99,100,102]}),
 ("ad", "Ad campaign → weekly sales index", "index", {"Control": [96,101,99,100,98], "Video": [110,112,108,115,111], "Search": [104,106,107,103,105]}),
 ("hosp", "Treatment protocol → recovery days", "days", {"Standard": [9,10,11,8,10], "Prot. B": [7,8,6,7,8], "Prot. C": [9,8,9,10,8]}),
 ("soil", "Soil treatment → plant height", "cm", {"None": [31,33,30,32,34], "Compost": [38,40,39,37,41], "Biochar": [35,36,34,37,36]}),
 ("call", "Call-centre training → handling time", "minutes", {"Old": [8.2,8.5,8.1,8.6,8.4], "Coached": [7.4,7.1,7.5,7.2,7.3], "Simul.": [6.8,6.9,6.7,7.0,6.6]}),
 ("elec", "Region → household electricity use", "index", {"North": [112,108,115,110,111], "South": [98,102,100,99,101], "West": [105,107,104,106,103], "East": [100,101,99,102,98]}),
 ("seed", "Seed variety → germination", "%", {"V1": [81,84,83,82,85], "V2": [90,88,91,89,92], "V3": [86,85,87,88,84]}),
 ("web", "Website layout → task time", "seconds", {"Classic": [54,58,55,57,56], "Compact": [49,47,50,48,51], "Guided": [43,45,44,42,46]}),
 # NEW: a null result and an unequal-variance case
 ("batt", "Battery brand → hours of life  (NEW: a null result)", "hours", {"Brand X": [9.8,10.6,10.1,9.5,10.4], "Brand Y": [10.3,9.7,10.8,9.9,10.0], "Brand Z": [10.4,9.9,10.7,11.0,10.0]}),
 ("courier", "Courier → delivery time  (NEW: unequal spreads)", "hours", {"Fast": [30,31,29,30,31], "Budget": [26,44,33,24,47], "Local": [34,36,35,37,34]}),
]
ONE = {}
for key, title, unit, g in EX:
    r = oneway(g); r.update(title=title, unit=unit); ONE[key] = r
R["oneway"] = ONE

# Tukey HSD for fertilizer
f = ONE["fert"]
tk = stats.tukey_hsd(*[np.array(d) for d in f["data"]])
ci = tk.confidence_interval(0.95)
pairs = []
for i, j in [(1, 0), (2, 0), (1, 2)]:
    pairs.append(dict(lab=f"{f['names'][i]} − {f['names'][j]}", diff=float(np.mean(f["data"][i]) - np.mean(f["data"][j])),
                      lo=float(ci.low[i, j]), hi=float(ci.high[i, j]), p=float(tk.pvalue[i, j])))
R["tukey"] = pairs

# ----------------------------------------------------------------- regression
D = np.array([[5,35,21.58],[8,45,21.22],[10,50,22.45],[12,55,22.08],[15,65,24.22],[18,70,24.35],
              [20,75,25.78],[24,85,25.52],[28,92,27.08],[32,100,27.1],[35,105,28.72],[40,115,29.28]])
X = np.c_[np.ones(12), D[:, :2]]; y = D[:, 2]
b, *_ = np.linalg.lstsq(X, y, rcond=None); fit = X @ b; res = y - fit
sse = (res ** 2).sum(); sst = ((y - y.mean()) ** 2).sum(); ssr = sst - sse
cov = np.linalg.inv(X.T @ X) * sse / 9; se = np.sqrt(np.diag(cov)); t = b / se
rr = np.corrcoef(D[:, 0], D[:, 1])[0, 1]
simple = [stats.linregress(D[:, j], y) for j in (0, 1)]
R["reg"] = dict(data=D.tolist(), b=b.tolist(), se=se.tolist(), t=t.tolist(),
                p=(2 * stats.t.sf(abs(t), 9)).tolist(), sse=sse, ssr=ssr, sst=sst,
                F=(ssr / 2) / (sse / 9), Fp=stats.f.sf((ssr / 2) / (sse / 9), 2, 9),
                r2=ssr / sst, adjr2=1 - (sse / 9) / (sst / 11), mse=sse / 9, totvar=sst / 11,
                r=rr, vif=1 / (1 - rr ** 2),
                simple=[dict(slope=s.slope, r2=s.rvalue ** 2, p=s.pvalue) for s in simple])

# ----------------------------------------------------------------- two-way
def twoway(cells):  # cells[a][b] -> list of reps (balanced)
    Y = np.array(cells, float)  # a x b x r
    A, B, r = Y.shape; gm = Y.mean()
    ma, mb, mab = Y.mean((1, 2)), Y.mean((0, 2)), Y.mean(2)
    ssa = B * r * ((ma - gm) ** 2).sum(); ssb = A * r * ((mb - gm) ** 2).sum()
    ssab = r * ((mab - ma[:, None] - mb[None, :] + gm) ** 2).sum()
    sse = ((Y - mab[:, :, None]) ** 2).sum(); sst = ((Y - gm) ** 2).sum()
    dfe = A * B * (r - 1); mse = sse / dfe
    rows = []
    for nm, ss, df in [("Variety (A)", ssa, A - 1), ("Irrigation (B)", ssb, B - 1), ("Variety × Irrigation", ssab, (A - 1) * (B - 1))]:
        Fv = (ss / df) / mse
        rows.append(dict(src=nm, ss=ss, df=df, ms=ss / df, F=Fv, p=stats.f.sf(Fv, df, dfe), peta=ss / (ss + sse)))
    rows.append(dict(src="Residual (within cells)", ss=sse, df=dfe, ms=mse))
    rows.append(dict(src="Total", ss=sst, df=A * B * r - 1))
    return dict(rows=rows, cellmeans=mab.tolist(), data=Y.tolist(), totvar=sst / (A * B * r - 1))

def mk(means):
    return [[[m - 1, m, m + 1] for m in row] for row in means]
TW_ADD = twoway(mk([[28, 31, 33], [32, 34, 37], [30, 33, 35]]))   # (nearly) parallel lines
TW_INT = twoway(mk([[28, 31, 33], [27, 33, 39], [33, 33, 32]]))   # crossing lines
R["tw_add"], R["tw_int"] = TW_ADD, TW_INT

# ----------------------------------------------------------------- cluster / ICC / DEFF
means = [42, 47, 51, 55, 60, 64, 68, 73]
PSU = np.array([[m + e for e in (-2, -1, 0, 1, 2)] for m in means], float)
a = PSU.ravel(); gm = a.mean(); sst = ((a - gm) ** 2).sum()
ssw = ((PSU - PSU.mean(1, keepdims=True)) ** 2).sum(); ssb = sst - ssw
msb, msw = ssb / 7, ssw / 32; m = 5
sb2 = max((msb - msw) / m, 0); icc = sb2 / (sb2 + msw); deff = 1 + (m - 1) * icc
R["psu"] = dict(data=PSU.tolist(), ssb=ssb, ssw=ssw, sst=sst, msb=msb, msw=msw, F=msb / msw,
                sb2=sb2, sw2=msw, icc=icc, deff=deff, neff=40 / deff, totvar=sst / 39)

# realistic Punjab-style example
n, m, rho, p = 2400, 12, 0.06, 0.35
deff = 1 + (m - 1) * rho; se_srs = np.sqrt(p * (1 - p) / n)
cvw = 0.5; deff_w = 1 + cvw ** 2
R["punjab"] = dict(n=n, m=m, k=n // m, rho=rho, p=p, deff=deff, deft=np.sqrt(deff), neff=n / deff,
                   se_srs=se_srs, moe_srs=1.96 * se_srs, moe_cl=1.96 * se_srs * np.sqrt(deff),
                   cvw=cvw, deff_w=deff_w, deff_tot=deff * deff_w, neff_tot=n / (deff * deff_w),
                   moe_tot=1.96 * se_srs * np.sqrt(deff * deff_w))
# cost-optimal cluster size
c1, c2 = 6000, 300
R["cost"] = dict(c1=c1, c2=c2, rho=0.06, mopt=np.sqrt(c1 / c2 * (1 - 0.06) / 0.06))

# simulation: SRS vs clustered sample of the same size
rng = np.random.default_rng(2026)
K, M, RHO, REPS = 40, 15, 0.15, 4000
sig_b, sig_w = np.sqrt(RHO), np.sqrt(1 - RHO)
srs = rng.normal(0, 1, (REPS, K * M)).mean(1)
clu = (rng.normal(0, sig_b, (REPS, K))[:, :, None] + rng.normal(0, sig_w, (REPS, K, M))).mean((1, 2))
R["sim"] = dict(K=K, M=M, rho=RHO, sd_srs=srs.std(), sd_clu=clu.std(),
                ratio=clu.var() / srs.var(), theory=1 + (M - 1) * RHO)

json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)

# ================================================================= FIGURES
def strip(ax, r, colors=GROUP, jitter=0.09, s=34, meanw=0.28, showgm=True):
    for i, (nm, d) in enumerate(zip(r["names"], r["data"])):
        c = colors[i % len(colors)]
        xs = i + np.linspace(-jitter, jitter, len(d))
        ax.scatter(xs, d, s=s, color=c, edgecolor="white", linewidth=1.2, zorder=3)
        ax.plot([i - meanw, i + meanw], [np.mean(d)] * 2, color=c, lw=2.5, solid_capstyle="round", zorder=2)
    if showgm:
        ax.axhline(r["gm"], color=INK2, lw=1, zorder=1)
    ax.set_xticks(range(len(r["names"])), r["names"]); ax.grid(axis="x", visible=False)
    ax.set_xlim(-0.6, len(r["names"]) - 0.4)

# Fig 1 — variance as literal squares: number line (top panel), squares (bottom panel)
fig, (at, ab) = plt.subplots(2, 1, figsize=(6.6, 3.6), gridspec_kw=dict(height_ratios=[1, 1.35], hspace=0.05))
v = np.array([4, 7, 8, 11, 15.]); mu = v.mean(); d = v - mu
at.plot([3.2, 15.8], [0, 0], color=AXIS, lw=1.2)
at.plot([mu, mu], [-0.3, 3.1], color=VIOLET, lw=1.8)
at.text(mu + 0.15, 3.1, f"mean = {mu:g}", color=VIOLET, ha="left", va="top", fontsize=9, weight="semibold")
heights = {4: 2.4, 7: 1.6, 8: 0.8, 11: 0.8, 15: 1.6}
for x, dv in zip(v, d):
    c = BLUE if dv < 0 else ORANGE; h = heights[int(x)]
    at.plot([x, x], [0, h], color=c, lw=0.8, alpha=0.45)
    at.annotate("", xy=(x, h), xytext=(mu, h), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.5, mutation_scale=9))
    at.text(x + (-0.15 if dv < 0 else 0.15), h, f"{dv:+g}", ha="right" if dv < 0 else "left", va="center", fontsize=8.5, color=c, weight="semibold")
    at.scatter([x], [0], s=55, color=c, edgecolor="white", lw=1.5, zorder=4)
    at.text(x, -0.35, f"{x:g}", ha="center", va="top", color=INK, fontsize=9, weight="semibold")
at.set_xlim(2.2, 16.8); at.set_ylim(-1.1, 3.75); at.axis("off")
at.text(2.2, 3.7, "① deviations from the mean", fontsize=8.5, color=INK2, va="top", weight="semibold")
x0, top = 0.3, 0
ab.text(0.3, 1.3, "② turn each deviation into a square", fontsize=8.5, color=INK2, va="bottom", weight="semibold")
for x, dv in zip(v, d):
    c = BLUE if dv < 0 else ORANGE; side = abs(dv); slot = max(side, 4.3); cx = x0 + slot / 2
    ab.add_patch(Rectangle((cx - side / 2, top - side), side, side, facecolor=c, alpha=0.2, edgecolor=c, lw=1.3))
    ab.text(cx, top - max(side, 1) - 0.3, f"({dv:+g})² = {dv*dv:g}", ha="center", va="top", fontsize=8.2, color=INK)
    x0 += slot + 0.8
ab.text(x0 + 0.2, -3.0, "③ add the areas\nSST = 70\ns² = 70 / 4 = 17.5", ha="left", va="center", fontsize=8.6, color=TOTAL, weight="semibold", linespacing=1.6)
ab.set_xlim(0, x0 + 6.8); ab.set_ylim(-7.3, 2.3); ab.set_aspect("equal"); ab.axis("off")
save(fig, "f_squares")

# Fig 2 — the decomposition of one point
r = ONE["fert"]
fig, ax = plt.subplots(figsize=(6.6, 3.5))
strip(ax, r, colors=["#9b9a94"] * 3, meanw=0.3, showgm=True)
for i, d in enumerate(r["data"]):
    ax.plot([i - .3, i + .3], [np.mean(d)] * 2, color=INK, lw=2.5, solid_capstyle="round", zorder=2)
# highlighted point: group B, value 26
xi, yv, gmean = 1 + 0.045, 26, r["means"][1]
ax.scatter([xi], [yv], s=80, color=INK, edgecolor="white", lw=1.5, zorder=5)
def arrow(x, y0, y1, c):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=11, color=c, lw=2, zorder=4))
arrow(xi + 0.52, r["gm"], yv, TOTAL); arrow(xi + 0.24, r["gm"], gmean, SIGNAL); arrow(xi + 0.24, gmean, yv, NOISE)
ax.text(xi + 0.6, (r["gm"] + yv) / 2, f"total\n{yv - r['gm']:+.2f}", color=TOTAL, va="center", fontsize=8.5, weight="semibold")
ax.text(xi + 0.12, (r["gm"] + gmean) / 2, f"between\n{gmean - r['gm']:+.2f}", color=SIGNAL, va="center", ha="right", fontsize=8.5, weight="semibold")
ax.text(xi + 0.12, (gmean + yv) / 2 + 0.05, f"within {yv - gmean:+.2f}", color=NOISE, va="center", ha="right", fontsize=8.5, weight="semibold")
ax.text(2.42, r["gm"] + 0.15, f"grand mean {r['gm']:.2f}", color=INK2, ha="right", va="bottom", fontsize=8)
ax.set_xticks(range(3), ["Fertilizer A", "Fertilizer B", "Fertilizer C"]); ax.set_ylabel("Yield (q/acre)")
ax.set_title("One observation, three deviations: total = between + within")
save(fig, "f_decomp")

# Fig 3 — SS budget bars for all 12 one-way examples
keys = [k for k, *_ in EX]
order = sorted(keys, key=lambda k: ONE[k]["eta"])
fig, ax = plt.subplots(figsize=(6.6, 3.9))
for yi, k in enumerate(order):
    e = ONE[k]["eta"]
    ax.barh(yi, e, color=SIGNAL, height=0.62, edgecolor="white", lw=1)
    ax.barh(yi, 1 - e, left=e, color=NOISE, alpha=0.9, height=0.62, edgecolor="white", lw=1)
    ax.text(-0.015, yi, ONE[k]["title"].split("  (")[0], ha="right", va="center", fontsize=8, color=INK)
    ax.text(e - 0.012 if e > 0.12 else e + 0.012, yi, f"{e:.0%}", ha="right" if e > 0.12 else "left",
            va="center", fontsize=7.5, color="white" if e > 0.12 else INK, weight="semibold")
ax.set_yticks([]); ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
ax.set_title("Share of the total sum of squares: signal (between) vs noise (within)")
ax.legend(handles=[Rectangle((0, 0), 1, 1, color=SIGNAL), Rectangle((0, 0), 1, 1, color=NOISE)],
          labels=["Between groups (η²)", "Within groups"], loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=2)
save(fig, "f_budget")

# Fig 4 — signal vs noise 2x2
rng2 = np.random.default_rng(7)
base = rng2.standard_normal((3, 8)); base = (base - base.mean(1, keepdims=True)) / base.std(1, ddof=1, keepdims=True)
fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.6), sharey=True)
for ri, gap in enumerate([3.0, 1.0]):
    for ci, sd in enumerate([0.8, 2.4]):
        ax = axes[ri, ci]
        g = {nm: list(20 + gap * (i - 1) + sd * base[i]) for i, nm in enumerate("ABC")}
        rr_ = oneway(g); strip(ax, rr_, s=22)
        ax.set_title(f"F = {rr_['F']:.1f},  " + ("p < 0.001" if rr_['p'] < 0.001 else f"p = {rr_['p']:.2f}"), fontsize=9)
        ax.text(0.98, 0.04, f"gap {gap:g} · spread {sd:g}", transform=ax.transAxes, ha="right", fontsize=7.5, color=MUTED)
axes[0, 0].set_ylabel("Large gaps between means"); axes[1, 0].set_ylabel("Small gaps between means")
axes[0, 0].annotate("Low noise", xy=(0.5, 1.28), xycoords="axes fraction", ha="center", weight="semibold", color=NOISE)
axes[0, 1].annotate("High noise", xy=(0.5, 1.28), xycoords="axes fraction", ha="center", weight="semibold", color=NOISE)
fig.tight_layout()
save(fig, "f_signalnoise")

# Fig 5 — the F distribution
fig, ax = plt.subplots(figsize=(6.6, 2.6))
x = np.linspace(0.001, 8, 600); dens = stats.f.pdf(x, 2, 12); fc = r["Fcrit"]
ax.plot(x, dens, color=INK, lw=1.8)
ax.fill_between(x, dens, where=x >= fc, color=ORANGE, alpha=0.35, lw=0)
ax.axvline(fc, color=ORANGE, lw=1.2)
ax.text(fc + 0.1, 0.55, f"critical F = {fc:.2f}\n(top 5% shaded)", color=INK2, fontsize=8)
ax.annotate(f"observed F = {r['F']:.1f}  →\n(far off the chart; p = {r['p']:.4f})", xy=(7.95, 0.05), ha="right", fontsize=8.5, color=ORANGE, weight="semibold")
ax.text(1.05, 0.9, "Under H₀, F usually lands near 1", color=INK2, fontsize=8)
ax.set_xlim(0, 8); ax.set_ylim(0, 1.05); ax.set_xlabel("F with (2, 12) degrees of freedom"); ax.set_ylabel("density")
ax.set_title("Where would F fall if all fertilizers were equally good?")
save(fig, "f_fdist")

# Fig 6 — gallery (small multiples)
fig, axes = plt.subplots(3, 4, figsize=(6.8, 6.4))
for ax, k in zip(axes.ravel(), keys):
    rr_ = ONE[k]; strip(ax, rr_, s=12, meanw=0.3, jitter=0.12)
    ax.set_title(rr_["title"].split("→")[1].split("(")[0].strip().capitalize(), fontsize=8, pad=4)
    ax.tick_params(labelsize=6.5); ax.set_xticks(range(rr_["k"]), [n[:6] for n in rr_["names"]], fontsize=6)
    ax.text(0.03, 0.97, f"η² {rr_['eta']:.2f}", transform=ax.transAxes, fontsize=7, va="top", color=INK, weight="semibold")
    if k in ("batt", "courier"):
        for s in ("left", "bottom"): ax.spines[s].set_color(MAGENTA); ax.spines[s].set_linewidth(1.6)
fig.tight_layout(h_pad=1.2, w_pad=0.6)
save(fig, "f_gallery")

# Fig 7 — Tukey intervals
fig, ax = plt.subplots(figsize=(6.6, 2.2))
for i, pr in enumerate(pairs):
    sig = pr["lo"] > 0 or pr["hi"] < 0; c = ORANGE if sig else MUTED
    ax.plot([pr["lo"], pr["hi"]], [i, i], color=c, lw=3, solid_capstyle="round")
    ax.scatter([pr["diff"]], [i], s=50, color=c, edgecolor="white", lw=1.5, zorder=3)
    ax.text(pr["hi"] + 0.15, i, f"{pr['diff']:+.1f}  (" + ("p < 0.001" if pr["p"] < 0.001 else f"p = {pr['p']:.3f}") + ")", va="center", fontsize=8, color=INK2)
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(range(3), [p_["lab"] for p_ in pairs]); ax.grid(axis="y", visible=False)
ax.set_xlabel("Difference in mean yield (q/acre), 95% family-wise interval"); ax.set_ylim(-0.6, 2.6); ax.set_xlim(-3.5, 8)
ax.set_title("Tukey HSD: which pairs of fertilizers differ?")
save(fig, "f_tukey")

# Fig 8 — residual diagnostics
resid = np.concatenate([np.array(d) - np.mean(d) for d in r["data"]])
fitted = np.concatenate([[np.mean(d)] * len(d) for d in r["data"]])
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.6))
for i in range(3):
    sl = slice(5 * i, 5 * i + 5)
    a1.scatter(fitted[sl] + np.linspace(-.08, .08, 5), resid[sl], s=30, color=GROUP[i], edgecolor="white", lw=1, label=r["names"][i])
a1.axhline(0, color=INK2, lw=1); a1.set_xlabel("fitted value (group mean)"); a1.set_ylabel("residual")
a1.set_title("Residuals vs fitted", fontsize=9); a1.legend(fontsize=7.5, loc="upper left", ncol=3, handletextpad=0.1)
a1.set_ylim(-3, 3.4)
(osm, osr), (sl_, ic, _) = stats.probplot(resid)
a2.plot(osm, sl_ * osm + ic, color=VIOLET, lw=1.4); a2.scatter(osm, osr, s=24, color=BLUE, edgecolor="white", lw=1)
a2.set_xlabel("theoretical normal quantile"); a2.set_ylabel("ordered residual"); a2.set_title("Normal Q–Q plot", fontsize=9)
fig.tight_layout(); save(fig, "f_diag")

# Fig 9 — regression: collinearity and fit
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.8))
a1.scatter(D[:, 0], D[:, 1], s=34, color=VIOLET, edgecolor="white", lw=1)
a1.set_xlabel("farm size (acres)"); a1.set_ylabel("fertilizer used (kg)")
a1.set_title(f"The two predictors move together\nr = {rr:.3f}", fontsize=9)
a2.plot([21, 30], [21, 30], color=AXIS, lw=1)
a2.scatter(fit, y, s=34, color=BLUE, edgecolor="white", lw=1)
a2.set_xlabel("predicted yield/acre"); a2.set_ylabel("observed yield/acre")
a2.set_title(f"…yet jointly they predict well\nR² = {R['reg']['r2']:.3f}", fontsize=9)
fig.tight_layout(); save(fig, "f_reg")

# Fig 10 — interaction plots
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), sharey=True)
irr = ["Low", "Medium", "High"]
for ax, tw, ttl in [(axes[0], TW_ADD, "No interaction: lines roughly parallel"), (axes[1], TW_INT, "Interaction: lines cross")]:
    for i, row in enumerate(tw["cellmeans"]):
        ax.plot(range(3), row, color=GROUP[i], marker="o", ms=6, mec="white", mew=1.2)
        ax.text(2.08, row[2], f"V{i+1}", color=INK, va="center", fontsize=8.5, weight="semibold")
    ax.set_xticks(range(3), irr); ax.set_xlabel("irrigation"); ax.set_title(ttl, fontsize=9); ax.set_xlim(-0.2, 2.35)
axes[0].set_ylabel("mean crop yield")
fig.tight_layout(); save(fig, "f_interact")

# Fig 11 — PSU strip
fig, ax = plt.subplots(figsize=(6.6, 2.9))
for i, row in enumerate(PSU):
    ax.scatter(i + np.linspace(-.1, .1, 5), row, s=22, color=NOISE, edgecolor="white", lw=0.8, zorder=3)
    ax.plot([i - .3, i + .3], [row.mean()] * 2, color=SIGNAL, lw=2.5, solid_capstyle="round")
ax.axhline(gm, color=TOTAL, lw=1.2); ax.text(7.45, gm + 1, f"grand mean {gm:.1f}", ha="right", color=TOTAL, fontsize=8)
ax.set_xticks(range(8), [f"PSU {i+1}" for i in range(8)]); ax.grid(axis="x", visible=False)
ax.set_ylabel("survey score"); ax.set_title("Tight inside each PSU (blue), far apart between PSUs (orange)")
save(fig, "f_psu")

# Fig 12 — variance shares for three ICC scenarios
fig, ax = plt.subplots(figsize=(6.6, 1.9))
sc = [("Typical attitude item", 0.03), ("Vote intention by booth", 0.10), ("Toy PSU example (§9.4)", icc)]
for yi, (lab, rho_) in enumerate(sc[::-1]):
    ax.barh(yi, rho_, color=SIGNAL, height=0.6, edgecolor="white"); ax.barh(yi, 1 - rho_, left=rho_, color=NOISE, height=0.6, edgecolor="white")
    ax.text(-0.015, yi, lab, ha="right", va="center", fontsize=8, color=INK)
    ax.text(min(rho_, 0.9) + 0.012 if rho_ < 0.5 else rho_ - 0.012, yi, f"ICC = {rho_:.2f}", va="center",
            ha="left" if rho_ < 0.5 else "right", fontsize=7.5, color="white", weight="semibold")
ax.set_yticks([]); ax.set_xlim(0, 1); ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
ax.legend(handles=[Rectangle((0, 0), 1, 1, color=SIGNAL), Rectangle((0, 0), 1, 1, color=NOISE)],
          labels=["between-cluster σ²_b", "within-cluster σ²_w"], loc="lower center", bbox_to_anchor=(0.5, -0.62), ncol=2, fontsize=8)
ax.set_title("ICC is the orange share of the total variance")
save(fig, "f_iccbars")

# Fig 13 — DEFF vs rho
fig, ax = plt.subplots(figsize=(6.6, 2.9))
rh = np.linspace(0, 0.3, 100)
for i, mm in enumerate([3, 5, 10, 20]):
    ax.plot(rh, 1 + (mm - 1) * rh, color=GROUP[i])
    ax.text(0.302, 1 + (mm - 1) * 0.3, f"m = {mm}", color=INK, va="center", fontsize=8.5, weight="semibold")
ax.set_xlim(0, 0.335); ax.set_xlabel("intraclass correlation ρ"); ax.set_ylabel("DEFF = 1 + (m−1)ρ")
ax.set_title("Design effect grows with both ρ and the number interviewed per cluster (m)")
save(fig, "f_deff")

# Fig 14 — simulation
fig, ax = plt.subplots(figsize=(6.6, 2.7))
bins = np.linspace(-0.35, 0.35, 70)
ax.hist(srs, bins=bins, color=BLUE, alpha=0.75, label=f"SRS of {K*M}: SD = {srs.std():.3f}", edgecolor="white", lw=0.4)
ax.hist(clu, bins=bins, color=ORANGE, alpha=0.55, label=f"{K} clusters × {M}: SD = {clu.std():.3f}", edgecolor="white", lw=0.4)
ax.set_xlabel("sample mean (true value = 0)"); ax.set_ylabel(f"count of {REPS:,} samples"); ax.legend(loc="upper left", fontsize=8)
ax.set_title(f"Same n = {K*M}, very different precision  (ρ = {RHO})")
ax.text(0.99, 0.95, f"variance ratio = {clu.var()/srs.var():.2f}\ntheory 1+(m−1)ρ = {1+(M-1)*RHO:.2f}", transform=ax.transAxes,
        ha="right", va="top", fontsize=8.5, color=INK, weight="semibold")
save(fig, "f_sim")

# Fig 15 — cost-optimal cluster size
fig, ax = plt.subplots(figsize=(6.6, 2.7))
budget = 1_200_000; ms = np.arange(2, 61)
for i, rho_ in enumerate([0.02, 0.06, 0.15]):
    k_ = budget / (c1 + c2 * ms); nn = k_ * ms; var = (1 + (ms - 1) * rho_) / nn
    rel = var / var.min(); ax.plot(ms, rel, color=GROUP[i])
    mo = np.sqrt(c1 / c2 * (1 - rho_) / rho_); j = np.argmin(var)
    ax.scatter([ms[j]], [1], color=GROUP[i], s=40, edgecolor="white", zorder=3)
    ax.text(ms[-1] + 0.8, rel[-1], f"ρ = {rho_}\nbest m ≈ {mo:.0f}", color=INK, fontsize=7.5, va="center")
ax.set_ylim(0.95, 2.0); ax.set_xlim(0, 70)
ax.set_xlabel("respondents interviewed per booth (m)"); ax.set_ylabel("variance relative to best")
ax.set_title("Fixed budget: ₹6,000 to open a booth, ₹300 per interview")
save(fig, "f_cost")

print(json.dumps({k: ONE[k]["F"] for k in ("batt", "courier")}), ONE["courier"]["welchF"], ONE["courier"]["welchp"], ONE["courier"]["p"])
print("tw add", [(x["src"], round(x["ss"], 2), round(x.get("F", 0), 2)) for x in TW_ADD["rows"]])
print("tw int", [(x["src"], round(x["ss"], 2), round(x.get("F", 0), 2)) for x in TW_INT["rows"]])
print("punjab", R["punjab"]); print("sim", R["sim"]); print("cost", R["cost"]); print("tukey", pairs)
