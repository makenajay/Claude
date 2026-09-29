// KaTeX-render body.html, wrap it, and print cover + body PDFs with Chromium.
const fs = require("fs"), path = require("path");
const katex = require("katex");
const { chromium } = require(path.join(process.env.NPM_ROOT, "playwright"));
const H = __dirname, B = path.join(H, "build");

const macros = {
  "\\SST": "\\textcolor{4a3aa7}{\\mathrm{SST}}", "\\SSB": "\\textcolor{b8461a}{\\mathrm{SSB}}",
  "\\SSW": "\\textcolor{1c5cab}{\\mathrm{SSW}}", "\\MSB": "\\textcolor{b8461a}{\\mathrm{MS}_B}",
  "\\MSW": "\\textcolor{1c5cab}{\\mathrm{MS}_W}",
};
const tex = (s, display) => katex.renderToString(s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">"),
  { displayMode: display, macros, throwOnError: true, strict: "ignore" });

function renderMath(html) {
  return html.split(/(<pre[\s\S]*?<\/pre>)/).map((part, i) => {
    if (i % 2) return part;
    part = part.replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => tex(m, true));
    return part.replace(/\$([^$\n]+?)\$/g, (_, m) => tex(m, false));
  }).join("");
}

fs.cpSync(path.join(H, "node_modules/katex/dist"), path.join(B, "katex"), { recursive: true });
const head = (title) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${title}</title>
<link rel="stylesheet" href="katex/katex.min.css"><link rel="stylesheet" href="style.css"></head><body>`;
fs.writeFileSync(path.join(B, "doc.html"), head("ANOVA from First Principles") + renderMath(fs.readFileSync(path.join(B, "body.html"), "utf8")) + "</body></html>");
fs.writeFileSync(path.join(B, "cover.html"), head("Cover") + `<style>@page{margin:0}</style>` + fs.readFileSync(path.join(H, "cover.html"), "utf8") + "</body></html>");

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME });
  const page = await browser.newPage();
  const foot = `<div style="width:100%;font-family:Inter,sans-serif;font-size:7.5pt;color:#898781;padding:0 17mm;display:flex;justify-content:space-between">
    <span>ANOVA from First Principles</span><span><b style="color:#4a3aa7">●</b> <span class="pageNumber"></span></span></div>`;
  await page.goto("file://" + path.join(B, "cover.html"), { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: path.join(B, "cover.pdf"), format: "A4", printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await page.goto("file://" + path.join(B, "doc.html"), { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: path.join(B, "body.pdf"), format: "A4", printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: "<span></span>", footerTemplate: foot });
  await browser.close();
  console.log("pdfs written");
})();
