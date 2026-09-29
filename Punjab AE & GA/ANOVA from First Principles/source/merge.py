import pymupdf, os
d = pymupdf.open("build/cover.pdf"); d.insert_pdf(pymupdf.open("build/body.pdf"))
d.set_metadata({"title": "ANOVA from First Principles (2nd edition)", "subject": "Variance decomposition, regression, signal vs noise, and survey design effects"})
d.save("build/ANOVA.pdf", garbage=3, deflate=True)
print("pages", len(d), os.path.getsize("build/ANOVA.pdf") // 1024, "KB")
os.makedirs("pages", exist_ok=True)
for f in os.listdir("pages"): os.remove("pages/" + f)
for i, p in enumerate(d): p.get_pixmap(dpi=55).save(f"pages/p{i+1:02d}.png")
